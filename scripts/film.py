"""Portfolio film, native video players, chapters, and localized timed captions."""
import json
from html import escape as E
from pathlib import Path
from i18n import LANGUAGES

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'content/film.json'


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}'


def clock(seconds):
    return f'{int(seconds) // 60:02}:{int(seconds) % 60:02}'


def excerpt_cues(film, start, end):
    return [{**cue, 'start': max(cue['start'], start) - start, 'end': min(cue['end'], end) - start}
            for cue in film['cues'] if cue['end'] > start and cue['start'] < end]


def write_captions():
    film = json.loads(DATA.read_text())
    editions = [('portfolio', 0, film['duration'])] + [(slug, clip['start'], clip['end']) for slug, clip in film['clips'].items()]
    for language in LANGUAGES:
        catalog = {} if language == 'en' else json.loads((ROOT / f'content/locales/{language}.json').read_text())
        for name, start, end in editions:
            cues = excerpt_cues(film, start, end)
            blocks = ['WEBVTT', '']
            for i, cue in enumerate(cues, 1):
                text = catalog.get(cue['text'], cue['text']) if language == 'en' else catalog[cue['text']]
                blocks.extend([str(i), f'{timestamp(cue["start"])} --> {timestamp(cue["end"])}', E(text), ''])
            (ROOT / f'assets/film/{name}.{language}.vtt').write_text('\n'.join(blocks).rstrip() + '\n')


def player(name, title, src, poster, cues, chapters=()):
    tracks = ''.join(f'<track kind="captions" src="/assets/film/{name}.{code}.vtt" srclang="{code}" label="{label}"{(" default" if code == "en" else "")}>' for code, (label, _) in LANGUAGES.items())
    options = '<option value="off">Off</option>' + ''.join(f'<option value="{code}" lang="{code}">{label}</option>' for code, (label, _) in LANGUAGES.items())
    chapter_list = ''
    if chapters:
        links = ''.join(f'<li><a href="{src}#t={chapter["start"]}" data-video-seek="{chapter["start"]}"><span class="chapter-time" dir="ltr">{clock(chapter["start"])}</span><span>{E(chapter["title"])}</span><span aria-hidden="true">↗</span></a></li>' for chapter in chapters)
        chapter_list = f'<nav class="film-chapters" aria-label="Film chapters"><h2>Jump to a chapter</h2><ol>{links}</ol></nav>'
    transcript = ''.join(f'<p><a href="{src}#t={cue["start"]}" data-video-seek="{cue["start"]}"><span dir="ltr">{clock(cue["start"])}</span></a> <span>{E(cue["text"])}</span></p>' for cue in cues)
    return f'''<div class="film-player" data-film-player="{name}">
<video id="video-{name}" controls playsinline preload="none" width="1920" height="1080" poster="{poster}" aria-label="{E(title, quote=True)}"><source src="{src}" type="video/mp4">{tracks}<a href="{src}">Download video</a></video>
<div class="film-tools"><label class="caption-control" hidden>Captions <select data-captions aria-controls="video-{name}">{options}</select></label><a class="text-link" href="{src}" download>Download video <span aria-hidden="true">↓</span></a></div>
<p class="film-language-note">English audio. Captions are available in all ten site languages; translations are machine-assisted.</p>
{chapter_list}<details class="film-transcript"><summary>Read the transcript</summary><div>{transcript}</div></details>
<p class="film-error" role="status" hidden>Playback could not start. Try the video controls or download the video.</p></div>'''


def film_body():
    film = json.loads(DATA.read_text())
    video = player('portfolio', 'Shengbo Jiang portfolio film', '/assets/film/shengbo-portfolio-v8.mp4', '/assets/film/portfolio-poster.webp', film['cues'], film['chapters'])
    return f'''<section class="film-intro shell"><span class="eyebrow">PORTFOLIO FILM <span dir="ltr">/ 02:00</span></span><h1>The work,<br><em>in motion.</em></h1><p>Two minutes inside the work: simulations, signals, particles, and language in motion.</p></section>
<section class="film-stage shell" aria-label="Portfolio video">{video}</section>
<section class="film-connections shell"><div><span class="eyebrow">CONTINUE EXPLORING</span><h2>Behind the demonstrations.</h2><p>The film shows experiments and work in progress. Explore the project pages for methods, context, and limitations.</p></div><div class="film-project-links"><a href="/work/sailbot/"><span>01 / Kehillah Sailbot</span><strong>Navigation, forces, and simulation</strong><span aria-hidden="true">↗</span></a><a href="/work/sign-translator/"><span>02 / Sign-Translator</span><strong>Reconstructing and generating motion</strong><span aria-hidden="true">↗</span></a></div></section>
<section class="contact-strip shell"><p>More from my video channel.</p><a class="text-link" href="https://www.youtube.com/@Luckyknight324" target="_blank" rel="noopener noreferrer">YouTube <span aria-hidden="true">↗</span></a></section>'''


def project_film(slug):
    film = json.loads(DATA.read_text())
    if slug not in film['clips']:
        return ''
    clip = film['clips'][slug]
    video = player(slug, clip['title'], f'/assets/film/{slug}-excerpt.mp4', clip['poster'], excerpt_cues(film, clip['start'], clip['end']))
    return f'''<section class="project-film shell" aria-labelledby="project-film-heading"><div class="section-heading"><div><span class="eyebrow">FROM MY PORTFOLIO FILM</span><h2 id="project-film-heading">{E(clip['title'])}</h2></div><a class="text-link" href="/film/#t={clip['start']}">Watch the full film <span aria-hidden="true">↗</span></a></div>{video}<p class="media-caption">{E(clip['description'])}</p></section>'''
