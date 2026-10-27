# Shengbo Jiang — personal portfolio

A complete, static, multi-page portfolio. The design uses warm ivory, forest green, editorial typography, custom project illustrations, and original project media. No framework, package installation, or client-side router is required.

## Preview

From this directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173/. Use an HTTP server rather than opening HTML files directly, because internal URLs are root-relative.

## Edit and build

- `content/projects.json`: project copy, facts, links, and ordering.
- `scripts/build.py`: shared HTML components and Home, Work, About, Contact, and project-page layouts.
- `styles.css`: design tokens, page layouts, responsive styles, and reduced-motion support.
- `scripts/asset_pipeline.py`: bundles fonts with the stylesheet and gives CSS/JS content-hashed filenames. Every generated page references the exact matching bundle, avoiding stale CDN/browser caches.
- `app.js`: mobile navigation, work filtering, email copying, and compatibility redirects for former homepage anchors.
- `assets/`: self-hosted fonts, optimized images, résumé, original project video, and transcript.
- `SOURCES.md`: source provenance and editorial decisions.

```sh
python3 scripts/build.py
python3 scripts/check.py
node --check app.js
python3 scripts/package.py
```

Build and check scripts use only the Python standard library. Generated HTML is committed alongside its sources so the repository can be served without a build step. After changing source content, rerun the builder.

`package.py` creates a clean `dist/` containing only public files. It refuses to overwrite a pre-existing directory without its build marker. Deploy the **contents of `dist/`** at the root of a static host. Preserve directory index handling (`/work/releaf/` → `work/releaf/index.html`). `_headers` and `_redirects` retain the existing host conventions; other hosts may need equivalent configuration. Packaging itself does not publish. The existing hosting integration deploys changes pushed to `main`.

## Pages and behavior

- Home: introduction and four selected projects.
- Work: eight projects; Product, Research, and Teams filters. Filter state is reflected in the URL.
- Eight dedicated case studies with roles, project context, original media, and further-reading links.
- About: biography, experience, tools, and recognition.
- Contact: email, copy action, and public profiles.
- A custom 404 page.

Pages, links, résumé download, and the native video player work without JavaScript. Filtering and the compact mobile menu progressively enhance the HTML. Keyboard focus, Escape-to-close, reduced motion, local fonts, and alternative image text are included. The original project video has on-screen narration text; a separate text transcript is linked beside it. The video uses `preload="none"` and is fetched only when played.

## Validation completed

- 13 HTML pages and 194 local references passed the static checker.
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
