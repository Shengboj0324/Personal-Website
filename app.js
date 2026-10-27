'use strict';

// Core content and navigation remain usable without JavaScript.
document.documentElement.classList.add('js');

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#primary-nav');
const mobileViewport = window.matchMedia('(max-width: 700px)');

function setMenu(open, restoreFocus = false) {
  if (!menuButton || !navigation) return;
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
  navigation.classList.toggle('is-open', open);
  document.body.classList.toggle('menu-open', open);
  const symbol = menuButton.querySelector('span');
  if (symbol) symbol.textContent = open ? '−' : '+';
  if (restoreFocus) menuButton.focus();
}

menuButton?.addEventListener('click', () => {
  setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
});

navigation?.addEventListener('click', (event) => {
  if (event.target instanceof Element && event.target.closest('a')) setMenu(false);
});

// Keep keyboard focus inside the mobile menu while its overlay is open.
document.addEventListener('keydown', (event) => {
  if (menuButton?.getAttribute('aria-expanded') !== 'true') return;
  if (event.key === 'Escape') {
    setMenu(false, true);
  } else if (event.key === 'Tab' && navigation) {
    const links = [...navigation.querySelectorAll('a[href]')];
    const last = links.at(-1);
    if (event.shiftKey && document.activeElement === menuButton && last) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      menuButton.focus();
    }
  }
});
mobileViewport.addEventListener('change', () => setMenu(false));

const filterBar = document.querySelector('.filter-bar');
if (filterBar) {
  const filterButtons = [...filterBar.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('.project-card[data-category]')];
  const count = document.querySelector('#filter-count');
  const allowedFilters = filterButtons.map((button) => button.dataset.filter);

  function applyFilter(value, updateURL = false) {
    const filter = allowedFilters.includes(value) ? value : 'All';
    let visibleCount = 0;
    for (const card of cards) {
      card.hidden = filter !== 'All' && card.dataset.category !== filter;
      if (!card.hidden) visibleCount += 1;
    }
    for (const button of filterButtons) {
      button.setAttribute('aria-pressed', String(button.dataset.filter === filter));
    }
    if (count) count.textContent = `${visibleCount} ${visibleCount === 1 ? 'project' : 'projects'}`;
    if (updateURL) {
      const url = new URL(window.location.href);
      if (filter === 'All') url.searchParams.delete('category');
      else url.searchParams.set('category', filter);
      window.history.replaceState(null, '', url);
    }
  }

  filterBar.hidden = false;
  applyFilter(new URLSearchParams(window.location.search).get('category'));
  for (const button of filterButtons) {
    button.addEventListener('click', () => applyFilter(button.dataset.filter, true));
  }
  window.addEventListener('popstate', () => {
    applyFilter(new URLSearchParams(window.location.search).get('category'));
  });
}

const copyButton = document.querySelector('[data-copy]');
if (copyButton && navigator.clipboard?.writeText) {
  copyButton.hidden = false;
  copyButton.addEventListener('click', async () => {
    const status = document.querySelector('.copy-status');
    try {
      await navigator.clipboard.writeText(copyButton.dataset.copy);
      if (status) status.textContent = 'Email address copied.';
    } catch {
      if (status) status.textContent = 'Copy unavailable. Select the email address above, or click it to write.';
    }
  });
}

// An original, illustrative water surface. Navigation remains ordinary HTML.
function createLiquidSurface(deck, reducedMotion, motionButton) {
  const canvas = deck.querySelector('.water-canvas');
  let context;
  try { context = canvas?.getContext('2d'); } catch { return null; }
  if (!context) return null;
  const markers = [...deck.querySelectorAll('.record-stop')].map((node) => ({
    x: parseFloat(node.style.left) * 5, y: parseFloat(node.style.top) * 5,
  }));
  let frame = 0;
  let last = 0;
  let time = 0;
  let angle = 0;
  let selected = 0;
  let energy = 0;
  let paused = false;
  let visible = true;
  let size = 500;
  let wake = [];
  const lightCanvas = document.createElement('canvas');
  lightCanvas.width = 128; lightCanvas.height = 128;
  const lightContext = lightCanvas.getContext('2d');
  const lightPixels = lightContext?.createImageData(128, 128);

  function caustics() {
    if (!lightContext || !lightPixels) return;
    const cells = Array.from({length: 18}, (_, i) => ({
      x: ((i * 0.618034) % 1) * 1.3 - 0.15 + Math.sin(time * 0.24 + i * 2) * 0.035,
      y: ((i * 0.414214) % 1) * 1.3 - 0.15 + Math.cos(time * 0.2 + i * 3) * 0.035,
    }));
    for (let y = 0; y < 128; y++) {
      for (let x = 0; x < 128; x++) {
        const u = x / 128, v = y / 128;
        const wx = u + 0.042 * Math.sin(v * 19 + time * 0.7 + angle * 0.12)
          + 0.018 * Math.cos(u * 29 + v * 11 - time * 0.6);
        const wy = v + 0.038 * Math.sin(u * 17 - time * 0.5)
          + 0.02 * Math.cos(v * 25 + u * 9 + time * 0.4);
        let nearest = Infinity, second = Infinity;
        for (const cell of cells) {
          const distance = (wx - cell.x) ** 2 + (wy - cell.y) ** 2;
          if (distance < nearest) { second = nearest; nearest = distance; }
          else if (distance < second) second = distance;
        }
        const intensity = Math.exp(-(Math.sqrt(second) - Math.sqrt(nearest)) * 110);
        const offset = (y * 128 + x) * 4;
        lightPixels.data[offset] = 250;
        lightPixels.data[offset + 1] = 255;
        lightPixels.data[offset + 2] = 231;
        lightPixels.data[offset + 3] = Math.round(intensity * (80 + 40 * (1 - v)));
      }
    }
    lightContext.putImageData(lightPixels, 0, 0);
  }

  function outline() {
    const points = Array.from({length: 48}, (_, i) => {
      const a = i / 48 * Math.PI * 2;
      const radius = 186 + 13 * Math.sin(3 * a + time * 0.32)
        + 9 * Math.cos(5 * a - time * 0.21) + energy * 7 * Math.sin(4 * a + angle);
      return {x: 250 + Math.cos(a) * radius * 1.04, y: 250 + Math.sin(a) * radius * 0.99};
    });
    const path = new Path2D();
    const first = points[0], end = points.at(-1);
    path.moveTo((first.x + end.x) / 2, (first.y + end.y) / 2);
    points.forEach((p, i) => {
      const next = points[(i + 1) % points.length];
      path.quadraticCurveTo(p.x, p.y, (p.x + next.x) / 2, (p.y + next.y) / 2);
    });
    path.closePath();
    return path;
  }

  function draw(now = performance.now()) {
    const c = context;
    c.setTransform(size / 500, 0, 0, size / 500, 0, 0);
    c.clearRect(0, 0, 500, 500);
    const shape = outline();
    const base = c.createLinearGradient(100, 50, 390, 460);
    base.addColorStop(0, '#e5eed3');
    base.addColorStop(0.42, '#a6d5c2');
    base.addColorStop(1, '#6b9f92');
    c.fillStyle = base;
    c.shadowColor = '#52766620'; c.shadowBlur = 16; c.shadowOffsetY = 8;
    c.fill(shape);
    c.shadowBlur = 0; c.shadowOffsetY = 0;
    c.save();
    c.clip(shape);
    // Broad, changing bands of refracted light, never concentric rings.
    c.save(); c.translate(250, 250); c.rotate(-0.35 + Math.sin(time * 0.13) * 0.1 + angle * 0.08); c.translate(-250, -250);
    for (let i = 0; i < 3; i++) {
      const y = 35 + i * 165;
      const bend = Math.sin(time * 0.65 + i * 1.7 + angle) * (32 + energy * 12);
      const width = 12 + 10 * Math.sin(i + time * 0.3);
      const light = c.createLinearGradient(0, y - 40, 480, y + 90);
      light.addColorStop(0, '#fffef100'); light.addColorStop(0.42, '#fffef130'); light.addColorStop(1, '#e4f1d000');
      c.beginPath(); c.moveTo(-70, y);
      c.bezierCurveTo(100, y - 90 + bend, 195, y + 115 - bend, 340, y + 10);
      c.bezierCurveTo(415, y - 45, 450, y + bend, 570, y - 40);
      c.lineTo(570, y - 40 + width);
      c.bezierCurveTo(450, y + bend + width, 415, y - 20, 340, y + 25);
      c.bezierCurveTo(195, y + 140 - bend, 100, y - 60 + bend, -70, y + width);
      c.closePath(); c.fillStyle = light; c.fill();
      c.beginPath(); c.moveTo(-70, y + width);
      c.bezierCurveTo(100, y - 60 + bend, 195, y + 140 - bend, 340, y + 25);
      c.bezierCurveTo(415, y - 20, 450, y + bend + width, 570, y - 40 + width);
      c.strokeStyle = '#faffed24'; c.lineWidth = 1.3; c.stroke();
    }
    c.restore();
    caustics();
    if (lightPixels) c.drawImage(lightCanvas, 0, 0, 500, 500);
    // Diffuse glints keep the material transparent rather than metallic.
    const glint = c.createRadialGradient(178, 150, 10, 210, 180, 210);
    glint.addColorStop(0, '#ffffeab0'); glint.addColorStop(0.45, '#f9ffe926'); glint.addColorStop(1, '#ffffff00');
    c.fillStyle = glint; c.fillRect(0, 0, 500, 500);
    const mark = markers[selected];
    const glow = c.createRadialGradient(mark.x, mark.y, 0, mark.x, mark.y, 95);
    glow.addColorStop(0, '#f9d39b80'); glow.addColorStop(1, '#f9d39b00');
    c.fillStyle = glow; c.fillRect(0, 0, 500, 500);
    for (let i = 0; i < 25; i++) {
      const x = 250 + Math.sin(i * 7.13 + time * 0.08) * 190;
      const y = 250 + Math.cos(i * 3.91 + time * 0.1) * 185;
      c.beginPath(); c.arc(x, y, 0.6 + (i % 3) * 0.35, 0, Math.PI * 2);
      c.fillStyle = '#faffed94'; c.fill();
    }
    wake = wake.filter((point) => now - point.at < 1400);
    for (let i = 1; i < wake.length; i++) {
      const a = wake[i - 1], b = wake[i];
      const life = Math.max(0, 1 - (now - b.at) / 1400);
      const curl = Math.sin((now - b.at) * 0.004 + i * 0.5) * (1 - life) * 18;
      c.beginPath(); c.moveTo(a.x, a.y);
      c.quadraticCurveTo((a.x + b.x) / 2 + curl, (a.y + b.y) / 2 - curl, b.x, b.y);
      c.lineCap = 'round'; c.lineWidth = 10 * life; c.strokeStyle = `rgba(250,255,238,${life * 0.15})`; c.stroke();
      c.lineWidth = 1.5 * life; c.strokeStyle = `rgba(250,255,238,${life * 0.65})`; c.stroke();
    }
    c.restore();
    c.strokeStyle = '#faffeb9c'; c.lineWidth = 1.5; c.stroke(shape);
  }

  function running() { return visible && !document.hidden && !paused && !reducedMotion.matches; }
  function tick(now) {
    frame = 0;
    if (!running()) return;
    if (now - last >= 32) {
      const elapsed = Math.min(64, now - last);
      time += elapsed / 1000; energy *= Math.exp(-elapsed / 450);
      last = now; draw(now);
    }
    frame = requestAnimationFrame(tick);
  }
  function refresh() {
    cancelAnimationFrame(frame); frame = 0;
    motionButton.disabled = reducedMotion.matches;
    motionButton.textContent = reducedMotion.matches ? 'Reduced motion' : paused ? 'Resume motion' : 'Pause motion';
    draw();
    if (running()) { last = performance.now(); frame = requestAnimationFrame(tick); }
  }
  new ResizeObserver(() => {
    const width = deck.getBoundingClientRect().width;
    if (!width) return;
    size = Math.round(width * Math.min(window.devicePixelRatio || 1, 2));
    canvas.width = size; canvas.height = size;
    draw();
  }).observe(deck);
  new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; refresh(); }).observe(deck);
  document.addEventListener('visibilitychange', refresh);
  reducedMotion.addEventListener('change', refresh);
  motionButton.addEventListener('click', () => { paused = !paused; refresh(); });
  motionButton.hidden = false;
  draw();
  canvas.hidden = false;
  deck.querySelector('.water-fallback').hidden = true;
  refresh();
  return {
    turn(degrees, projectIndex) {
      const next = degrees * Math.PI / 180;
      energy = Math.min(1, energy + Math.abs(next - angle) * 0.2);
      angle = next; selected = projectIndex;
      if (!running()) draw();
    },
    stir(event) {
      const bounds = deck.getBoundingClientRect();
      if (!bounds.width) return;
      const point = {x: (event.clientX - bounds.left) / bounds.width * 500,
        y: (event.clientY - bounds.top) / bounds.height * 500, at: performance.now()};
      const previous = wake.at(-1);
      if (previous && Math.hypot(previous.x - point.x, previous.y - point.y) < 4) return;
      wake.push(point); if (wake.length > 36) wake.shift();
      energy = Math.min(1, energy + 0.09);
      if (!running()) draw();
    },
  };
}

// A finite project selector: every turn changes a real destination.
const turntable = document.querySelector('.project-turntable');
if (turntable) {
  const deck = turntable.querySelector('.record-deck');
  const surface = turntable.querySelector('.record-surface');
  const stops = [...turntable.querySelectorAll('[data-record-index]')];
  const label = turntable.querySelector('.record-label');
  const title = turntable.querySelector('.record-title');
  const category = turntable.querySelector('.record-category');
  const description = turntable.querySelector('.record-description');
  const counter = turntable.querySelector('.record-count');
  const status = turntable.querySelector('.record-status');
  const step = 360 / stops.length;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const liquid = createLiquidSurface(deck, reducedMotion, turntable.querySelector('.water-motion'));
  let index = -1;
  let rotation = 0;
  let drag = null;
  let animation = 0;
  let suppressClick = false;

  const wrap = (value) => ((value % stops.length) + stops.length) % stops.length;
  const angleDelta = (value) => ((value % 360 + 540) % 360) - 180;

  function amplify(angle) {
    for (const [i, stop] of stops.entries()) {
      const distance = Math.abs(angleDelta(i * step - angle));
      const proximity = Math.max(0, 1 - distance / (step * 1.35));
      const weight = (1 - Math.cos(proximity * Math.PI)) / 2;
      stop.style.setProperty('--record-scale', (1 + weight * 0.48).toFixed(3));
      stop.style.setProperty('--record-layer', String(1 + Math.round(weight * 10)));
    }
  }

  function announce() {
    status.textContent = surface.getAttribute('aria-valuetext');
  }

  function render(angle) {
    rotation = angle;
    amplify(angle);
    const next = wrap(Math.round(angle / step));
    liquid?.turn(angle, next);
    if (next === index) return;
    index = next;
    const project = stops[index].dataset;
    surface.setAttribute('aria-valuenow', String(index + 1));
    surface.setAttribute('aria-valuetext', `${index + 1} of ${stops.length}: ${project.title}`);
    for (const [i, stop] of stops.entries()) {
      stop.setAttribute('aria-pressed', String(i === index));
    }
    title.textContent = project.title;
    category.textContent = project.category;
    description.textContent = project.summary;
    label.setAttribute('href', project.url);
    label.setAttribute('aria-label', `Open ${project.title} case study`);
    counter.textContent = `${String(index + 1).padStart(2, '0')} / ${String(stops.length).padStart(2, '0')}`;
  }

  function stopAnimation() {
    cancelAnimationFrame(animation);
    animation = 0;
  }

  function settle(target = Math.round(rotation / step) * step) {
    stopAnimation();
    const start = rotation;
    const started = performance.now();
    if (reducedMotion.matches || Math.abs(target - start) < 0.1) {
      render(target);
      announce();
      return;
    }
    function tick(now) {
      const progress = Math.min(1, (now - started) / 220);
      render(start + (target - start) * (1 - (1 - progress) ** 3));
      if (progress < 1) animation = requestAnimationFrame(tick);
      else {
        animation = 0;
        announce();
      }
    }
    animation = requestAnimationFrame(tick);
  }

  function coast(velocity) {
    stopAnimation();
    if (reducedMotion.matches || Math.abs(velocity) < 0.02) {
      settle();
      return;
    }
    let last = performance.now();
    function tick(now) {
      const elapsed = Math.min(32, now - last);
      last = now;
      // Frame-rate-independent friction; the loop ends at the nearest project.
      const decay = Math.exp(-elapsed / 150);
      render(rotation + velocity * 150 * (1 - decay));
      velocity *= decay;
      if (Math.abs(velocity) > 0.015) animation = requestAnimationFrame(tick);
      else settle();
    }
    animation = requestAnimationFrame(tick);
  }

  function select(next) {
    settle(rotation + angleDelta(wrap(next) * step - rotation));
  }

  function pointerAngle(event) {
    const bounds = surface.getBoundingClientRect();
    const x = event.clientX - bounds.left - bounds.width / 2;
    const y = event.clientY - bounds.top - bounds.height / 2;
    // Near the center, tiny finger movements cannot define a reliable angle.
    if (Math.hypot(x, y) < bounds.width * 0.12) return null;
    return Math.atan2(x, -y) * 180 / Math.PI;
  }

  for (const [i, stop] of stops.entries()) {
    stop.hidden = false;
    stop.addEventListener('click', () => select(i));
    stop.addEventListener('focus', () => { if (!drag && !animation) amplify(i * step); });
  }
  for (const button of turntable.querySelectorAll('[data-record-step]')) {
    button.addEventListener('click', () => select(index + Number(button.dataset.recordStep)));
  }
  surface.hidden = false;
  turntable.querySelector('.record-controls').hidden = false;
  turntable.querySelector('.record-prompt').textContent = 'A FIELD OF IDEAS';
  render(0);

  surface.addEventListener('keydown', (event) => {
    const destinations = {
      ArrowRight: index + 1, ArrowUp: index + 1,
      ArrowLeft: index - 1, ArrowDown: index - 1,
      Home: 0, End: stops.length - 1,
    };
    if (!Object.hasOwn(destinations, event.key)) return;
    event.preventDefault();
    // Keyboard selection is immediate; reduced motion also skips all coasting.
    stopAnimation();
    render(rotation + angleDelta(wrap(destinations[event.key]) * step - rotation));
    announce();
  });

  deck.addEventListener('pointerdown', (event) => {
    const target = event.target instanceof Element
      ? event.target.closest('.record-surface, .record-stop') : null;
    if (!target || !event.isPrimary || event.button !== 0 || drag) return;
    stopAnimation();
    liquid?.stir(event);
    suppressClick = false;
    drag = {id: event.pointerId, target, startX: event.clientX, startY: event.clientY,
      startRotation: rotation, lastAngle: pointerAngle(event), lastTime: performance.now(),
      velocity: 0, moved: false};
    target.setPointerCapture(event.pointerId);
  });
  deck.addEventListener('pointermove', (event) => {
    if (!drag || event.pointerId === drag.id) liquid?.stir(event);
    const angle = pointerAngle(event);
    if (!drag) {
      if (!animation && event.pointerType === 'mouse') amplify(angle ?? rotation);
      return;
    }
    if (event.pointerId !== drag.id) return;
    const now = performance.now();
    const delta = angle === null || drag.lastAngle === null ? 0 : angleDelta(angle - drag.lastAngle);
    const elapsed = Math.max(1, now - drag.lastTime);
    drag.velocity = drag.velocity * 0.35 + Math.max(-1.2, Math.min(1.2, delta / elapsed)) * 0.65;
    drag.lastAngle = angle;
    drag.lastTime = now;
    if (Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 6) {
      drag.moved = true;
      deck.classList.add('is-dragging');
    }
    if (drag.moved) render(rotation + delta);
  });
  deck.addEventListener('pointerleave', () => {
    if (!drag && !animation) amplify(rotation);
  });
  deck.addEventListener('dragstart', (event) => event.preventDefault());
  deck.addEventListener('click', (event) => {
    if (!suppressClick || event.detail === 0) return;
    // A drag starting on a marker must never become a selection click.
    event.preventDefault();
    event.stopImmediatePropagation();
    suppressClick = false;
  }, true);

  function finishDrag(event, cancelled = false) {
    if (!drag || event.pointerId !== drag.id) return;
    const gesture = drag;
    drag = null;
    deck.classList.remove('is-dragging');
    suppressClick = gesture.moved || cancelled;
    if (gesture.target.hasPointerCapture(event.pointerId)) gesture.target.releasePointerCapture(event.pointerId);
    if (cancelled) render(gesture.startRotation);
    else if (gesture.moved) {
      coast(performance.now() - gesture.lastTime < 100 ? gesture.velocity : 0);
    } else if (gesture.target === surface) {
      const angle = pointerAngle(event);
      if (angle !== null) select(Math.round(angle / step));
    }
    // A stationary tap on a marker retains its normal button action.
  }
  deck.addEventListener('pointerup', (event) => finishDrag(event));
  deck.addEventListener('pointercancel', (event) => finishDrag(event, true));
  deck.addEventListener('lostpointercapture', (event) => finishDrag(event, true));
  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches && animation) settle();
  });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) return;
    stopAnimation();
    if (drag) finishDrag({pointerId: drag.id}, true);
    render(Math.round(rotation / step) * step);
  });
}

// Preserve useful inbound anchors from the former single-page portfolio.
if (window.location.pathname === '/') {
  const legacyRoutes = {
    '#work': '/work/', '#about': '/about/', '#experience': '/about/',
    '#awards': '/about/', '#skills': '/about/', '#contact': '/contact/',
    '#resume': '/assets/shengbo-jiang-resume.pdf', '#releaf': '/work/releaf/',
    '#sign': '/work/sign-translator/', '#athena': '/work/college-advisor/',
    '#igem': '/work/igem/', '#sustai': '/work/releaf/',
  };
  const route = legacyRoutes[window.location.hash];
  if (route) window.location.replace(route);
}
