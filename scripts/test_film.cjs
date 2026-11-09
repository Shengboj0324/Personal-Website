'use strict';
const {readFileSync} = require('node:fs');
const {runInNewContext} = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const source = readFileSync(require('node:path').join(__dirname, '../app.js'), 'utf8');
const enhancement = source.slice(source.indexOf('// Native playback remains available without JavaScript;'));

function fixture(hash = '', locale = 'ja') {
  class Element {
    constructor() { this.events = {}; this.attributes = {}; this.dataset = {}; }
    addEventListener(name, fn) { (this.events[name] ??= []).push(fn); }
    emit(name, event = {}) { for (const fn of this.events[name] || []) fn(event); }
    setAttribute(name, value) { this.attributes[name] = value; }
    removeAttribute(name) { delete this.attributes[name]; }
    closest() { return this; }
  }
  const video = new Element();
  Object.assign(video, {readyState: 0, currentTime: 0, duration: 120, loads: 0, plays: 0,
    load() { this.loads++; }, play() { this.plays++; return Promise.resolve(); }, pause() {}});
  video.textTracks = Object.assign([{kind: 'captions', language: 'en'}, {kind: 'captions', language: 'ja'}], {addEventListener: video.addEventListener.bind(video)});
  const captions = new Element(), error = new Element(), player = new Element();
  const chapterLinks = [0, 12, 64].map(seconds => { const link = new Element(); link.dataset.videoSeek = String(seconds); return link; });
  player.dataset.filmPlayer = 'portfolio';
  player.querySelector = selector => ({video, '[data-captions]': captions, '.film-error': error})[selector];
  player.querySelectorAll = () => chapterLinks;
  const window = new Element(); window.location = {hash, href: `https://example.com/ja/film/${hash}`};
  window.history = {replaceState(_state, _title, url) { window.location.hash = url.hash; }};
  const document = {querySelectorAll: selector => selector === '[data-film-player]' ? [player] : [video]};
  runInNewContext(enhancement, {document, window, locale, Element, URLSearchParams, URL, updateLanguageLinks() {}});
  function click(link, options = {}) {
    let prevented = false;
    player.emit('click', {target: link, button: 0, preventDefault() { prevented = true; }, ...options});
    return prevented;
  }
  return {video, captions, player, error, chapterLinks, window, click};
}

test('normal page visit does not request or autoplay video; captions match page language', () => {
  const f = fixture();
  assert.equal(f.video.loads, 0); assert.equal(f.video.plays, 0);
  assert.equal(f.video.textTracks[0].mode, 'disabled'); assert.equal(f.video.textTracks[1].mode, 'showing');
  f.captions.value = 'off'; f.captions.emit('change');
  assert.ok(f.video.textTracks.every(track => track.mode === 'disabled'));
});

test('chapter click waits for metadata, seeks, plays, and preserves the chapter in the URL', () => {
  const f = fixture();
  assert.equal(f.click(f.chapterLinks[2]), true);
  assert.equal(f.video.loads, 1); assert.equal(f.video.plays, 1);
  f.video.readyState = 1; f.video.emit('loadedmetadata');
  assert.equal(f.video.currentTime, 64); assert.equal(f.window.location.hash, '#t=64');
  f.video.emit('timeupdate'); assert.equal(f.chapterLinks[2].attributes['aria-current'], 'true');
  assert.equal(f.chapterLinks[0].attributes['aria-current'], undefined);
});

test('shared chapter links seek without autoplay and invalid times do nothing', () => {
  const f = fixture('#t=12');
  f.video.readyState = 1; f.video.emit('loadedmetadata');
  assert.equal(f.video.currentTime, 12); assert.equal(f.video.plays, 0);
  const invalid = fixture('#t=NaN'); assert.equal(invalid.video.loads, 0);
  const negative = fixture('#t=-10'); assert.equal(negative.video.loads, 0);
});

test('modifier clicks retain ordinary media links and native caption changes update the selector', () => {
  const f = fixture();
  assert.equal(f.click(f.chapterLinks[1], {ctrlKey: true}), false); assert.equal(f.video.loads, 0);
  f.video.textTracks[0].mode = 'showing'; f.video.textTracks[1].mode = 'disabled'; f.video.emit('change');
  assert.equal(f.captions.value, 'en');
});
