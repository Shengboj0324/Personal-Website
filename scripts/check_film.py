#!/usr/bin/env python3
"""Validate the actual film assets, cue timing, and every localized player."""
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from film import DATA, ROOT, excerpt_cues, timestamp
from i18n import LANGUAGES

class MediaPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.players = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'video':
            self.current = {'attrs': attrs, 'tracks': []}
            self.players.append(self.current)
        if tag == 'track' and self.current is not None:
            self.current['tracks'].append(attrs)
    def handle_endtag(self, tag):
        if tag == 'video': self.current = None

film = json.loads(DATA.read_text())
previous = 0
assert film['cues'], 'The transcript is empty'
for cue in film['cues']:
    assert previous <= cue['start'] < cue['end'] <= film['duration'], cue
    assert cue['text'].strip() and '-->' not in cue['text'], cue
    previous = cue['end']
assert all(a['start'] < b['start'] for a, b in zip(film['chapters'], film['chapters'][1:]))
media = [('portfolio', 'shengbo-portfolio-v8.mp4', 0, film['duration'])]
media += [(name, f'{name}-excerpt.mp4', clip['start'], clip['end']) for name, clip in film['clips'].items()]
for name, filename, start, end in media:
    path = ROOT / 'assets/film' / filename
    assert 0 < path.stat().st_size < 25 * 1024**2, f'{path}: exceeds host asset limit'
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))
    assert abs(float(probe['format']['duration']) - (end-start)) < .15, filename
    assert any(s['codec_name'] == 'h264' and s['width'] == 1920 for s in probe['streams']), filename
    assert any(s['codec_name'] == 'aac' for s in probe['streams']), filename
    data = path.read_bytes()
    assert data.index(b'moov') < data.index(b'mdat'), f'{filename}: missing faststart metadata'
    expected = excerpt_cues(film, start, end)
    for language in LANGUAGES:
        vtt = (ROOT / f'assets/film/{name}.{language}.vtt').read_text()
        assert vtt.startswith('WEBVTT\n\n')
        timings = re.findall(r'^(\d\d:\d\d:\d\d\.\d{3}) --> (\d\d:\d\d:\d\d\.\d{3})$', vtt, re.M)
        assert timings == [(timestamp(c['start']), timestamp(c['end'])) for c in expected], (name, language)
        blocks = vtt.strip().split('\n\n')[1:]
        assert all(len(block.splitlines()) >= 3 and block.splitlines()[2].strip() for block in blocks)

for language, (_, prefix) in LANGUAGES.items():
    for route in ['film', 'work/sailbot', 'work/sign-translator']:
        path = ROOT / prefix / route / 'index.html'
        page = MediaPage(); page.feed(path.read_text())
        players = [p for p in page.players if p['attrs'].get('id', '').startswith('video-')]
        assert len(players) == 1, path
        player = players[0]
        assert all(key in player['attrs'] for key in ['controls', 'playsinline', 'poster']), path
        assert player['attrs']['preload'] == 'none' and 'autoplay' not in player['attrs'], path
        assert sorted(t['srclang'] for t in player['tracks']) == sorted(LANGUAGES), path
        assert [t['srclang'] for t in player['tracks'] if 'default' in t] == [language], path
print(f'PASS: {len(media)} optimized videos, {len(media)*len(LANGUAGES)} timed caption tracks, and 30 localized players.')
