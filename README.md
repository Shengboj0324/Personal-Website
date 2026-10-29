# Shengbo Jiang — personal portfolio

A complete, static, multi-page portfolio. The design uses warm ivory, forest green, editorial typography, custom project illustrations, and original project media. No framework, package installation, or client-side router is required.

## Preview

From this directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173/. Use an HTTP server rather than opening HTML files directly, because internal URLs are root-relative.

## Edit and build

- `content/projects.json`: project copy, facts, links, ordering, and optional `technical` sections (heading, three modules, footnote, and source link).
- `scripts/build.py`: shared HTML components and Home, Work, About, Contact, and project-page layouts.
- `scripts/i18n.py`: static language editions, localized routes, same-page language links, metadata, and strict translation coverage.
- `content/locales/`: checked-in translation catalogs and the complete localized heading with inline emphasis. English source text is the catalog key; add translations for new copy before building.
- `styles.css`: design tokens, page layouts, responsive styles, and reduced-motion support.
- `scripts/asset_pipeline.py`: bundles fonts with the stylesheet and gives CSS/JS content-hashed filenames. Every generated page references the exact matching bundle, avoiding stale CDN/browser caches.
- `app.js`: the liquid project explorer, mobile navigation, work filtering, email copying, and compatibility redirects for former homepage anchors.
- `assets/`: self-hosted fonts, optimized images, résumé, original project video, and transcript.
- `SOURCES.md`: source provenance and editorial decisions.

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 scripts/test_i18n.py
node --check app.js
node --test scripts/test_turntable.cjs
python3 scripts/package.py
```

Build and check scripts use only the Python standard library. Generated HTML is committed alongside its sources so the repository can be served without a build step. After changing source content, rerun the builder.

`package.py` creates a clean `dist/` containing only public files. It refuses to overwrite a pre-existing directory without its build marker. Deploy the **contents of `dist/`** at the root of a static host. Preserve directory index handling (`/work/releaf/` → `work/releaf/index.html`). `_headers` and `_redirects` retain the existing host conventions; other hosts may need equivalent configuration. Packaging itself does not publish. The existing hosting integration deploys changes pushed to `main`.

## Pages and behavior

- Home: introduction, an interactive liquid field containing eight project markers, and four selected projects. Drag around the water, select a marker, use previous/next, or focus the surface and use arrow keys (Home/End select the first/last project). The title link beneath the water opens the selected case study.
- Work: eight projects; Product, Research, and Teams filters. Filter state is reflected in the URL.
- Eight dedicated case studies with roles, project context, original media, and further-reading links. Seven technical projects include an engineering section; Sign-Translator also includes original rig imagery, four repository diagrams, and native expandable research notes.
- About: biography, experience, tools, and recognition.
- Contact: email, copy action, and public profiles.
- A custom 404 page.

Pages, links, résumé download, and the native video player work without JavaScript. Filtering and the compact mobile menu progressively enhance the HTML. Keyboard focus, Escape-to-close, reduced motion, local fonts, and alternative image text are included. The original project video has on-screen narration text; a separate text transcript is linked beside it. The video uses `preload="none"` and is fetched only when played.

The water is an original Canvas 2D illustration: a slowly deforming outline, procedural refracted light, diffuse highlights, and a bounded pointer wake. It is not a physical fluid solver. Ambient rendering is capped at approximately 30 frames per second; active pointer wakes render at display cadence. Rendering stops outside the viewport or in a hidden tab and can be paused. The expensive light texture is cached between updates, at most once per 64 milliseconds. Reduced-motion preferences disable ambient movement and animated settling; direct input still updates the surface and selection. Canvas resolution is capped at 2× device scale, and the light texture is computed at 128×128 pixels.

Touch gestures on the surface are reserved for unrestricted turning; the surrounding page scrolls normally. Pointer capture keeps dragging coherent beyond the surface, cancelled gestures restore the starting angle, and marker drags suppress trailing clicks. A center dead zone prevents angular jumps. Angular proximity, hover, and keyboard focus magnify nearby markers. Touch selection follows the absolute finger bearing from first contact, using the actual marker positions. Movement is applied once per display frame with no easing delay. Release settles to the nearest marker without inertial overshoot. There is no external library, sound, or wheel-scroll interception. Without JavaScript or canvas support, an original SVG illustration and the initial project link remain available. See `SOURCES.md` for design and interaction references.

## Validation completed

- 130 HTML pages across ten languages and 3,440 local references passed the static checker.
- All 120 content routes checked at 320, 390, 768, 901, 1024, and 1280 CSS pixels: 720 layout checks with no page or prose overflow.
- Localization regression tests cover internal routes versus external/media URLs, filter identifiers, escaping, missing copy, same-page language options, and Arabic document direction.
- Language switching preserves the current page, fragment, and active project filter; the language selector and localized navigation also work without JavaScript.
- Browser inspection of Home, Work, About, Contact, and the assay case study.
- All 12 content routes checked in browser frames at 320, 390, and 768 CSS pixels: no page overflow.
- Work filtering, mobile navigation, and email copying exercised through the UI.
- Local video playback verified (260.54-second duration, progressing playback, no media error).
- Source links and content checked against the supplied résumé, public Hugging Face model card, Kaggle profile/writeup/models, and relevant public repositories.

The older design/specification files and original `images/` remain as historical material; they are excluded from `dist/`. They are not the current content baseline.

## Production cache regression

The original host cached `/styles.css` and `/app.js` for one year with `immutable`. Reusing those URLs allowed old assets to survive a new HTML deployment. Generated pages now use `/assets/portfolio.<content-hash>.css` and `.js`; the CSS includes the local font declarations directly. `scripts/check.py` rejects unversioned references, incorrect bundle bytes, and page/bundle mismatches. Keep previously generated hashed bundles available for browsers with older HTML.

After the host has deployed a commit, verify the actual domain rather than relying on a local preview:

```sh
python3 scripts/check_live.py https://www.shengbojiang.me/
```

This checks every content route for the expected CSS/JS filenames and compares the deployed bundle bytes with the local build. A stale or incomplete deployment fails the check.

## Languages

English remains at `/`. The additional editions are Simplified Chinese (`/zh-hans/`), Traditional Chinese (`/zh-hant/`), Japanese (`/ja/`), Korean (`/ko/`), Hindi (`/hi/`), Spanish (`/es/`), French (`/fr/`), German (`/de/`), and Arabic (`/ar/`). Each has all twelve content pages and a translated 404 document. Visitors choose a language explicitly; there is no location-based redirect or external translation widget.

The header selector links to the equivalent page. Internal navigation retains the chosen language; JavaScript additionally preserves query parameters and fragments when switching. Filters keep stable internal identifiers while labels and status messages are localized. Canonical and `hreflang` links describe the corresponding editions. The host's fallback 404 remains the English root document, which includes the language selector.

Typography uses native Chinese/Japanese/Korean font stacks and normal upright emphasis for CJK text. Arabic uses self-hosted Noto Sans Arabic and Noto Naskh Arabic, right-to-left navigation and reading order, and isolated left-to-right media geometry and email addresses. Hindi uses self-hosted Noto Sans Devanagari and Noto Serif Devanagari with upright emphasis and room for vowel marks and conjuncts. Korean keeps words together where possible. Longer translated headings wrap naturally; cards, controls, and metadata do not rely on English text lengths. The original English headline remains unchanged.

Long-form translation drafts were machine-assisted from the public English website. The headline, key interface wording, project summaries, names, and selected technical caveats were refined manually. These have not received a professional native-speaker review in every language. Original screenshots, diagrams, video, downloadable transcript, and résumé retain their source language, with explanatory labels in translated pages. No translation service is contacted during builds or visits; catalogs are local files. Build validation rejects missing text, empty translations, and changed interpolation placeholders.

Touch tracking regression checks cover opposite-side contact, clockwise and counterclockwise sweeps, angle wrapping, the center dead zone, rapid input, release, cancellation, secondary pointers, and keyboard selection. These are event-handler tests; the October 29 touch fix could not be visually checked because local browser use was disabled in Work settings.
