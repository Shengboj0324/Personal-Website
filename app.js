'use strict';

// Core content and navigation remain usable without JavaScript.
document.documentElement.classList.add('js');

const locale = document.documentElement.lang || 'en';
const localePrefix = document.documentElement.dataset.localePrefix || '';
const localeMessages = JSON.parse(document.querySelector('#locale-messages')?.textContent || '{}');
const localNumber = new Intl.NumberFormat(locale);
const localPlural = new Intl.PluralRules(locale);
function t(key, values = {}) {
  return (localeMessages[key] || key).replace(/\{(\w+)\}/g, (match, name) => values[name] ?? match);
}

// Native details and links work without JavaScript; preserve page context on change.
const languagePicker = document.querySelector('.language-picker');
function updateLanguageLinks() {
  for (const link of languagePicker?.querySelectorAll('a[hreflang]') || []) {
    const url = new URL(link.href);
    url.search = window.location.search;
    url.hash = window.location.hash;
    link.href = url.href;
  }
}
updateLanguageLinks();
languagePicker?.addEventListener('toggle', () => {
  if (languagePicker.open) {
    updateLanguageLinks();
    setMenu(false);
  }
});
document.addEventListener('click', (event) => {
  if (languagePicker?.open && !languagePicker.contains(event.target)) languagePicker.open = false;
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && languagePicker?.open) {
    languagePicker.open = false;
    languagePicker.querySelector('summary').focus();
  }
});

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#primary-nav');
const mobileViewport = window.matchMedia('(max-width: 900px)');

function setMenu(open, restoreFocus = false) {
  if (!menuButton || !navigation) return;
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', t(open ? 'menuClose' : 'menuOpen'));
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
    if (count) {
      const plural = localPlural.select(visibleCount);
      count.textContent = t(plural === 'one' ? 'countOne' : plural === 'two' ? 'countTwo' : 'countMany', {count: localNumber.format(visibleCount)});
    }
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
      if (status) status.textContent = t('copied');
    } catch {
      if (status) status.textContent = t('copyFailed');
    }
  });
}

// Preserve useful inbound anchors from the former single-page portfolio.
if (window.location.pathname === `${localePrefix}/`) {
  const legacyRoutes = {
    '#work': '/work/', '#about': '/about/', '#experience': '/about/',
    '#awards': '/about/', '#skills': '/about/', '#contact': '/contact/',
    '#resume': '/assets/shengbo-jiang-resume.pdf', '#releaf': '/work/releaf/',
    '#sign': '/work/sign-translator/', '#athena': '/work/college-advisor/',
    '#igem': '/work/igem/', '#sustai': '/work/releaf/', '#selected-work': '/work/',
  };
  const route = legacyRoutes[window.location.hash];
  if (route) window.location.replace(route.startsWith('/assets/') ? route : localePrefix + route);
}

// Native playback remains available without JavaScript; enhance chapters and captions.
for (const player of document.querySelectorAll('[data-film-player]')) {
  const video = player.querySelector('video');
  const captions = player.querySelector('[data-captions]');
  const error = player.querySelector('.film-error');
  const chapterLinks = [...player.querySelectorAll('.film-chapters [data-video-seek]')];
  let pendingSeek = null;

  function showCaptions(language) {
    for (const track of video.textTracks) {
      if (track.kind === 'captions') track.mode = track.language === language ? 'showing' : 'disabled';
    }
  }
  captions.value = locale;
  showCaptions(locale);
  captions.closest('label').hidden = false;
  captions.addEventListener('change', () => showCaptions(captions.value));
  video.textTracks.addEventListener('change', () => {
    const showing = [...video.textTracks].find(track => track.kind === 'captions' && track.mode === 'showing');
    captions.value = showing?.language || 'off';
  });

  function applySeek() {
    if (pendingSeek === null || video.readyState < 1) return;
    video.currentTime = Math.min(pendingSeek, Number.isFinite(video.duration) ? Math.max(0, video.duration - 0.01) : pendingSeek);
    pendingSeek = null;
  }
  function seek(seconds, play = false) {
    if (!Number.isFinite(seconds) || seconds < 0) return;
    pendingSeek = seconds;
    error.hidden = true;
    if (video.readyState >= 1) applySeek();
    else {
      video.preload = 'metadata';
      video.load();
    }
    if (play) video.play().catch(() => { error.hidden = false; });
  }
  video.addEventListener('loadedmetadata', applySeek);
  video.addEventListener('error', () => { error.hidden = false; });
  video.addEventListener('playing', () => { error.hidden = true; });
  video.addEventListener('play', () => {
    for (const other of document.querySelectorAll('video')) if (other !== video) other.pause();
  });
  player.addEventListener('click', (event) => {
    const link = event.target instanceof Element ? event.target.closest('a[data-video-seek]') : null;
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const seconds = Number(link.dataset.videoSeek);
    if (!Number.isFinite(seconds) || seconds < 0) return;
    event.preventDefault();
    seek(seconds, true);
    if (player.dataset.filmPlayer === 'portfolio') {
      const url = new URL(window.location.href);
      url.hash = `t=${seconds}`;
      window.history.replaceState(null, '', url);
      updateLanguageLinks();
    }
  });
  video.addEventListener('timeupdate', () => {
    const active = chapterLinks.findLast(link => Number(link.dataset.videoSeek) <= video.currentTime);
    for (const link of chapterLinks) {
      if (link === active) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    }
  });
  if (player.dataset.filmPlayer === 'portfolio') {
    const seekFromHash = () => {
      const value = new URLSearchParams(window.location.hash.slice(1)).get('t');
      if (value !== null && /^\d+(\.\d+)?$/.test(value)) seek(Number(value));
    };
    seekFromHash();
    window.addEventListener('hashchange', seekFromHash);
  }
}
