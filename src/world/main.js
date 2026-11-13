// Entry point for the 3D layer. Pages work without it; this upgrades them when WebGL is available.
import { pickTier, supportsWebGL } from './core.js';
import { startViewer } from './viewer.js';
import { startVoyage } from './voyage.js';

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
const optedIn = () => { try { return sessionStorage.getItem('voyage-motion') === 'on'; } catch { return false; } };

// A soft procedural sea, off until the visitor asks for it. No audio files are downloaded.
function seaSound(button) {
  let context = null;
  let gain = null;
  button.hidden = false;
  button.addEventListener('click', async () => {
    const on = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', String(on));
    if (!context) {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (!Audio) return;
      context = new Audio();
      const length = context.sampleRate * 4;
      const buffer = context.createBuffer(1, length, context.sampleRate);
      const samples = buffer.getChannelData(0);
      let lastValue = 0;
      for (let i = 0; i < length; i++) {
        lastValue = (lastValue + 0.02 * (Math.random() * 2 - 1)) / 1.02;
        samples[i] = lastValue * 3.5;
      }
      const source = context.createBufferSource();
      source.buffer = buffer;
      source.loop = true;
      const filter = context.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.value = 520;
      const swell = context.createGain();
      const lfo = context.createOscillator();
      const lfoDepth = context.createGain();
      lfo.frequency.value = 0.11;
      lfoDepth.gain.value = 0.35;
      swell.gain.value = 0.6;
      lfo.connect(lfoDepth).connect(swell.gain);
      gain = context.createGain();
      gain.gain.value = 0;
      source.connect(filter).connect(swell).connect(gain).connect(context.destination);
      source.start();
      lfo.start();
    }
    await context.resume();
    gain.gain.linearRampToValueAtTime(on ? 0.5 : 0, context.currentTime + 0.8);
  });
}

async function voyage(root) {
  const enable = root.querySelector('[data-voyage-enable]');
  const launch = async () => {
    root.classList.add('is-live');
    try {
      await startVoyage(root, pickTier());
      const sound = root.querySelector('[data-sound]');
      if (sound) seaSound(sound);
    } catch (error) {
      console.warn('3D voyage unavailable:', error);
      root.classList.remove('is-live', 'is-ready');
    }
  };
  if (reduced.matches && !optedIn()) {
    if (enable) {
      enable.hidden = false;
      enable.addEventListener('click', () => {
        try { sessionStorage.setItem('voyage-motion', 'on'); } catch { /* private mode */ }
        enable.hidden = true;
        window.scrollTo(0, 0);
        launch();
      }, { once: true });
    }
    return;
  }
  await launch();
}

async function viewer(root) {
  try {
    root.classList.add('is-live');
    await startViewer(root, pickTier(), { still: reduced.matches });
  } catch (error) {
    console.warn('3D island unavailable:', error);
    root.classList.remove('is-live', 'is-ready');
  }
}

// ?static shows the page as it reads without the 3D layer.
if (supportsWebGL() && !window.location.search.includes('static')) {
  document.documentElement.classList.add('webgl');
  const home = document.querySelector('[data-voyage]');
  if (home) voyage(home);
  for (const island of document.querySelectorAll('[data-island]')) viewer(island);
}
