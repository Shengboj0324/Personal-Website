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
    deck.style.setProperty('--record-angle', `${angle}deg`);
    amplify(angle);
    const next = wrap(Math.round(angle / step));
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
      // Frame-rate-independent friction; the loop ends when the disc settles.
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
    // At the spindle, tiny finger movements cannot define a reliable angle.
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
  turntable.querySelector('.record-prompt').textContent = 'SPIN THROUGH THE WORK';
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
  });

  deck.addEventListener('pointerdown', (event) => {
    const target = event.target instanceof Element
      ? event.target.closest('.record-surface, .record-label, .record-stop') : null;
    if (!target || !event.isPrimary || event.button !== 0 || drag) return;
    stopAnimation();
    suppressClick = false;
    drag = {id: event.pointerId, target, startX: event.clientX, startY: event.clientY,
      startRotation: rotation, lastAngle: pointerAngle(event), lastTime: performance.now(),
      velocity: 0, moved: false};
    target.setPointerCapture(event.pointerId);
  });
  deck.addEventListener('pointermove', (event) => {
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
    // A drag starting on the center link or a dot must never become a click.
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
    // A stationary tap on a link or button retains its normal native action.
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
