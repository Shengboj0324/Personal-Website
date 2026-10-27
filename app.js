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
