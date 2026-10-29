'use strict';

// Exercise the shipped selector event handlers without a browser dependency.
const {readFileSync} = require('node:fs');
const {runInNewContext} = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const source = readFileSync(require('node:path').join(__dirname, '../app.js'), 'utf8');
const selector = source.slice(source.indexOf('// A finite project selector:'), source.indexOf('// Preserve useful inbound anchors'));
const positions = [[54, 15], [79, 28], [86, 53], [70, 77], [44, 86], [20, 73], [13, 45], [27, 21]];

function fixture(reduced = false) {
  class Element {
    constructor() {
      this.events = {}; this.attributes = {}; this.captured = new Set();
      this.style = {setProperty(name, value) { this[name] = value; }};
      this.classList = {add() {}, remove() {}};
    }
    addEventListener(type, fn) { (this.events[type] ??= []).push(fn); }
    emit(type, event = {}) { for (const fn of this.events[type] || []) fn(event); }
    setAttribute(name, value) { this.attributes[name] = value; }
    getAttribute(name) { return this.attributes[name]; }
    setPointerCapture(id) { this.captured.add(id); }
    hasPointerCapture(id) { return this.captured.has(id); }
    releasePointerCapture(id) { this.captured.delete(id); }
    closest() { return this; }
    getBoundingClientRect() { return {left: 0, top: 0, width: 500, height: 500}; }
  }
  const nodes = Object.fromEntries(['record-deck', 'record-surface', 'record-label', 'record-title', 'record-category', 'record-description', 'record-count', 'record-status', 'record-controls', 'water-motion'].map(name => [name, new Element()]));
  const stops = positions.map(([x, y], i) => {
    const node = new Element(); node.style.left = `${x}%`; node.style.top = `${y}%`;
    node.dataset = {title: `Project ${i + 1}`, category: 'Research', summary: 'Summary', url: `/work/${i}/`};
    return node;
  });
  const table = {querySelector: key => nodes[key.slice(1)], querySelectorAll: key => key === '[data-record-index]' ? stops : []};
  const document = new Element(); document.querySelector = () => table;
  const media = new Element(); media.matches = reduced;
  let now = 0, id = 0, lastAngle = 0;
  const frames = new Map();
  runInNewContext(selector, {
    document, Element, window: {matchMedia: () => media}, locale: 'en',
    localNumber: new Intl.NumberFormat('en'), projectNumber: new Intl.NumberFormat('en'),
    t: (key, values) => JSON.stringify({key, ...values}), performance: {now: () => now},
    requestAnimationFrame: fn => { frames.set(++id, fn); return id; },
    cancelAnimationFrame: key => frames.delete(key),
    createLiquidSurface: () => ({turn: angle => { lastAngle = angle; }, stir() {}}),
  });
  const deck = nodes['record-deck'], surface = nodes['record-surface'];
  function pointer(type, x, y, options = {}) {
    deck.emit(type, {target: surface, pointerId: 1, isPrimary: true, button: 0, pointerType: 'touch', clientX: x * 5, clientY: y * 5, ...options});
  }
  function frame(ms = 16) {
    now += ms;
    const callbacks = [...frames.values()]; frames.clear();
    for (const fn of callbacks) fn(now);
  }
  return {pointer, frame, deck, surface, stops, nodes, get angle() { return lastAngle; }, get selected() { return Number(surface.getAttribute('aria-valuenow')); }};
}

test('touching any marker follows that finger, regardless of the previous selection', () => {
  const f = fixture(true);
  for (const i of [4, 0, 6, 2, 7, 3, 1, 5]) {
    f.pointer('pointerdown', ...positions[i]);
    assert.equal(f.selected, i + 1);
    assert.equal(f.stops[i].style['--record-scale'], '1.480');
    f.pointer('pointerup', ...positions[i]);
  }
});

test('clockwise and counterclockwise sweeps follow the newest position each frame', () => {
  const f = fixture();
  f.pointer('pointerdown', ...positions[4]);
  for (const i of [5, 6, 7, 0, 1, 2, 3, 4, 3, 2, 1, 0, 7]) {
    f.pointer('pointermove', ...positions[i]); f.frame();
    assert.equal(f.selected, i + 1);
  }
});

test('crossing north unwraps to a small continuous turn', () => {
  const f = fixture();
  f.pointer('pointerdown', 49, 15); const before = f.angle;
  f.pointer('pointermove', 51, 15); f.frame();
  assert.ok(f.angle > before && f.angle - before < 4);
});

test('center dead zone is stable and reacquires the finger on the opposite side', () => {
  const f = fixture();
  f.pointer('pointerdown', ...positions[0]);
  f.pointer('pointermove', 50, 50); f.frame(); assert.equal(f.selected, 1);
  f.pointer('pointermove', ...positions[4]); f.frame(); assert.equal(f.selected, 5);
});

test('event bursts use the latest sample and release does not coast past the destination', () => {
  const f = fixture();
  f.pointer('pointerdown', ...positions[0]);
  f.pointer('pointermove', ...positions[1]);
  f.pointer('pointermove', ...positions[2]);
  f.frame(); assert.equal(f.selected, 3);
  f.pointer('pointermove', ...positions[3]);
  f.pointer('pointerup', ...positions[4]);
  assert.equal(f.selected, 5);
  for (let i = 0; i < 40; i++) f.frame();
  assert.equal(f.selected, 5);
  let blocked = false;
  f.deck.emit('click', {detail: 1, preventDefault() { blocked = true; }, stopImmediatePropagation() {}});
  assert.equal(blocked, true);
});

test('a second finger cannot steal the gesture and cancellation restores the prior choice', () => {
  const f = fixture();
  f.pointer('pointerdown', ...positions[4]);
  f.pointer('pointermove', ...positions[2], {pointerId: 2}); f.frame(); assert.equal(f.selected, 5);
  f.pointer('pointercancel', ...positions[4]); assert.equal(f.selected, 1);
  f.frame(); assert.equal(f.selected, 1);
});

test('keyboard and marker selection still work without motion', () => {
  const f = fixture(true);
  f.surface.emit('keydown', {key: 'End', preventDefault() {}}); assert.equal(f.selected, 8);
  f.surface.emit('keydown', {key: 'ArrowRight', preventDefault() {}}); assert.equal(f.selected, 1);
  f.stops[3].emit('click'); assert.equal(f.selected, 4);
  assert.equal(f.nodes['record-label'].getAttribute('href'), '/work/3/');
});
