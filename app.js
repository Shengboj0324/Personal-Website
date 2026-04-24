/* Shengbo Jiang — Portfolio interactions
   Vanilla JS: nav state, mobile menu, reveal, counters, hero canvas, CTA canvas.
   ========================================================================= */

(() => {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $  = (q, el = document) => el.querySelector(q);
  const $$ = (q, el = document) => Array.from(el.querySelectorAll(q));

  /* ---------- Footer year ---------- */
  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- Navigation: scroll state + section-aware theme ---------- */
  const nav = $('#nav');
  const darkSections = ['top', 'sign', 'astrobio', 'contact'];
  const onScroll = () => {
    if (!nav) return;
    const y = window.scrollY;
    nav.classList.toggle('is-scrolled', y > 24);

    // Decide light/dark based on which section the nav overlaps.
    let theme = 'dark';
    const navBottom = 72;
    for (const id of ['top','metrics','work','about','releaf','sustai','sign','athena','igem','astrobio','experience','awards','skills','faq','contact']) {
      const el = document.getElementById(id);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.top <= navBottom && r.bottom > navBottom) {
        theme = darkSections.includes(id) ? 'dark' : 'light';
        break;
      }
    }
    nav.classList.toggle('is-light', theme === 'light');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile menu ---------- */
  const burger = $('.nav__burger');
  const mobile = $('#mobileMenu');
  if (burger && mobile) {
    const close = () => {
      burger.setAttribute('aria-expanded', 'false');
      mobile.classList.remove('is-open');
      mobile.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    };
    const open = () => {
      burger.setAttribute('aria-expanded', 'true');
      mobile.classList.add('is-open');
      mobile.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    };
    burger.addEventListener('click', () => {
      burger.getAttribute('aria-expanded') === 'true' ? close() : open();
    });
    $$('.mobile-menu a').forEach(a => a.addEventListener('click', close));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }

  /* ---------- Reveal on scroll ---------- */
  const revealEls = $$('section, .project, .metric, .award, .skill-col, .dual__card, .timeline__item, .faq__item, .cta__card, .workflow__step, .pipeline__row, .challenges > div, .engine-grid > div, .roadmap__step, .arch__node, .about__pillars article');
  revealEls.forEach(el => el.classList.add('reveal'));
  if ('IntersectionObserver' in window && !prefersReduced) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-in'));
  }

  /* ---------- Count-up metrics ---------- */
  const counters = $$('[data-count-to]');
  const runCount = (el) => {
    const target = parseFloat(el.dataset.countTo);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 1600;
    const start = performance.now();
    const format = (n) => {
      const rounded = target >= 100 ? Math.round(n) : Math.round(n * 10) / 10;
      return prefix + rounded.toLocaleString('en-US') + suffix;
    };
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = format(target * eased);
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = format(target);
    };
    requestAnimationFrame(tick);
  };
  if ('IntersectionObserver' in window && !prefersReduced) {
    const cio = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { runCount(e.target); cio.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    counters.forEach(c => cio.observe(c));
  } else {
    counters.forEach(c => {
      const target = parseFloat(c.dataset.countTo);
      c.textContent = (c.dataset.prefix || '') + target.toLocaleString('en-US') + (c.dataset.suffix || '');
    });
  }

  /* ---------- Smooth anchor scroll with nav offset ---------- */
  $$('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (!id || id === '#' || id.length < 2) return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      const y = target.getBoundingClientRect().top + window.scrollY - 70;
      window.scrollTo({ top: y, behavior: prefersReduced ? 'auto' : 'smooth' });
    });
  });

  /* ---------- Canvas: particle constellation ---------- */
  const makeConstellation = (canvas, opts = {}) => {
    if (!canvas || prefersReduced) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    const {
      density = 0.00012,
      maxLink = 140,
      color = 'rgba(167, 139, 250, 0.75)',
      linkColor = 'rgba(167, 139, 250, 0.22)',
      speed = 0.35,
    } = opts;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w = 0, h = 0, points = [], mouse = { x: -9999, y: -9999 };
    let raf = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.max(30, Math.floor(w * h * density));
      points = new Array(count).fill(0).map(() => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * speed,
        vy: (Math.random() - 0.5) * speed,
        r: Math.random() * 1.4 + 0.4,
      }));
    };

    const loop = () => {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        const dx = p.x - mouse.x, dy = p.y - mouse.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 140 * 140) {
          const f = (1 - d2 / (140 * 140)) * 0.6;
          p.x += dx * 0.003 * f;
          p.y += dy * 0.003 * f;
        }

        ctx.beginPath();
        ctx.fillStyle = color;
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      for (let i = 0; i < points.length; i++) {
        for (let j = i + 1; j < points.length; j++) {
          const a = points[i], b = points[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < maxLink * maxLink) {
            const alpha = 1 - Math.sqrt(d2) / maxLink;
            ctx.strokeStyle = linkColor.replace(/[\d.]+\)$/, (alpha * 0.55).toFixed(3) + ')');
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(loop);
    };

    const onMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const pt = e.touches ? e.touches[0] : e;
      mouse.x = pt.clientX - rect.left;
      mouse.y = pt.clientY - rect.top;
    };
    const onLeave = () => { mouse.x = -9999; mouse.y = -9999; };

    resize();
    loop();
    window.addEventListener('resize', resize);
    const host = canvas.parentElement || canvas;
    host.addEventListener('mousemove', onMove);
    host.addEventListener('mouseleave', onLeave);
    host.addEventListener('touchmove', onMove, { passive: true });

    // Pause when offscreen
    const vio = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { if (!raf) loop(); }
      else { cancelAnimationFrame(raf); raf = 0; }
    }, { threshold: 0.01 });
    vio.observe(canvas);
  };

  makeConstellation($('#heroCanvas'), {
    density: 0.00014,
    maxLink: 150,
    color: 'rgba(186, 160, 255, 0.75)',
    linkColor: 'rgba(125, 211, 252, 0.30)',
    speed: 0.32,
  });
  makeConstellation($('#ctaCanvas'), {
    density: 0.00009,
    maxLink: 130,
    color: 'rgba(125, 211, 252, 0.65)',
    linkColor: 'rgba(139, 92, 246, 0.28)',
    speed: 0.28,
  });
})();
