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
  let index = 0;
  let rotation = 0;
  let drag = null;

  const wrap = (value) => ((value % stops.length) + stops.length) % stops.length;

  function render(angle, announce = true) {
    const next = wrap(Math.round(angle / step));
    const changed = next !== index;
    index = next;
    rotation = angle;
    deck.style.setProperty('--record-angle', `${angle}deg`);
    const project = stops[index].dataset;
    const position = `${index + 1} of ${stops.length}: ${project.title}`;
    surface.setAttribute('aria-valuenow', String(index + 1));
    surface.setAttribute('aria-valuetext', position);
    for (const [i, stop] of stops.entries()) {
      stop.setAttribute('aria-pressed', String(i === index));
    }
    title.textContent = project.title;
    category.textContent = project.category;
    description.textContent = project.summary;
    label.setAttribute('href', project.url);
    label.setAttribute('aria-label', `Open ${project.title} case study`);
    counter.textContent = `${String(index + 1).padStart(2, '0')} / ${String(stops.length).padStart(2, '0')}`;
    // The slider announces its own value. Other controls use a polite status.
    if (announce && changed && document.activeElement !== surface) {
      status.textContent = position;
    }
  }

  function select(next) {
    const target = wrap(next) * step;
    // Take the shortest path, including across the last/first project boundary.
    const delta = ((target - rotation) % 360 + 540) % 360 - 180;
    render(rotation + delta);
  }

  function angleAt(event) {
    const bounds = surface.getBoundingClientRect();
    return Math.atan2(event.clientX - bounds.left - bounds.width / 2,
      -(event.clientY - bounds.top - bounds.height / 2)) * 180 / Math.PI;
  }

  for (const stop of stops) {
    stop.hidden = false;
    stop.addEventListener('click', () => select(Number(stop.dataset.recordIndex)));
  }
  for (const button of turntable.querySelectorAll('[data-record-step]')) {
    button.addEventListener('click', () => select(index + Number(button.dataset.recordStep)));
  }
  surface.hidden = false;
  turntable.querySelector('.record-controls').hidden = false;
  turntable.querySelector('.record-prompt').textContent = 'SPIN THROUGH THE WORK';
  render(0, false);

  surface.addEventListener('keydown', (event) => {
    const destinations = {
      ArrowRight: index + 1, ArrowUp: index + 1,
      ArrowLeft: index - 1, ArrowDown: index - 1,
      Home: 0, End: stops.length - 1,
    };
    if (!Object.hasOwn(destinations, event.key)) return;
    event.preventDefault();
    select(destinations[event.key]);
  });

  surface.addEventListener('pointerdown', (event) => {
    if (!event.isPrimary || event.button !== 0 || drag) return;
    drag = {id: event.pointerId, startX: event.clientX, startY: event.clientY,
      startRotation: rotation, lastAngle: angleAt(event), travel: 0, moved: false};
    surface.setPointerCapture(event.pointerId);
  });
  surface.addEventListener('pointermove', (event) => {
    if (!drag || event.pointerId !== drag.id) return;
    const angle = angleAt(event);
    const delta = ((angle - drag.lastAngle + 540) % 360) - 180;
    drag.travel += delta;
    drag.lastAngle = angle;
    if (Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 6) {
      drag.moved = true;
      deck.classList.add('is-dragging');
    }
    if (drag.moved) render(drag.startRotation + drag.travel, false);
  });

  function finishDrag(event, cancelled = false) {
    if (!drag || event.pointerId !== drag.id) return;
    const gesture = drag;
    drag = null;
    deck.classList.remove('is-dragging');
    if (surface.hasPointerCapture(event.pointerId)) surface.releasePointerCapture(event.pointerId);
    if (cancelled) render(gesture.startRotation, false);
    else {
      if (gesture.moved) render(Math.round(rotation / step) * step, false);
      else select(Math.round(angleAt(event) / step));
      status.textContent = surface.getAttribute('aria-valuetext');
    }
  }
  surface.addEventListener('pointerup', (event) => finishDrag(event));
  surface.addEventListener('pointercancel', (event) => finishDrag(event, true));
  surface.addEventListener('lostpointercapture', (event) => finishDrag(event, true));
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
