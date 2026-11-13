# Shengbo Jiang — personal portfolio

A static, multi-page portfolio built around a 3D voyage. The home page is a small sea: a sailboat carries the visitor from a home harbor past eight islands, one per project, and ends on a chart of the whole route. Every island was modelled and lit in Blender for this site, baked to a texture, and drawn in the browser with three.js. Case studies open with their island, which can be turned by hand and has numbered points of interest.

There is no framework and no client-side router. Pages, links, the résumé download and the native video players work without JavaScript; without WebGL the voyage reads as an illustrated sequence.

## Preview

From this directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173/. Use an HTTP server rather than opening HTML files directly, because internal URLs are root-relative. Add `?static` to any URL to see the page without the 3D layer.

## Where things live

- `content/projects.json`: project copy, facts, links, the four island captions (`hotspots`), stated limits, connections to other projects, and the voyage narration (`tour`, `bridge`).
- `content/voyage.json`: sailing order, island spacing and radii, and the opening and closing text.
- `scripts/build.py`: shared HTML components and every page layout. Needs Python 3.12 or newer.
- `scripts/i18n.py` and `content/locales/`: static language editions and strict translation coverage. English source text is the catalog key; add translations for new copy before building.
- `styles.css`: design tokens, layouts, the voyage overlay, responsive rules, per-script typography and reduced-motion support.
- `app.js`: mobile navigation, language links, work filtering, email copying, film chapters and captions.
- `src/world/`: the 3D layer. `voyage.js` (home page), `viewer.js` (case-study island), `ocean.js` (sea shader), `core.js` (loading, baked materials, small animations), `main.js` (entry and fallbacks).
- `world.js`: the bundled 3D layer (three.js plus `src/world`). Rebuild with `npm install` once, then `npm run world`.
- `studio/`: the Blender source for the islands. `kit.py` is the shared modelling, lighting, baking and export library; `islands/*.py` builds each island; `STYLE.md` is the art direction; `produce.sh` bakes and packages. Not deployed with the site's pages, but kept in the repository so every model can be rebuilt.
- `assets/world/`: shipped 3D assets. Per island: `<slug>.glb` (Draco-compressed geometry), `<slug>.webp` and `<slug>-1k.webp` (baked light atlas), `<slug>-hero.webp` and `<slug>-card.webp` (Cycles stills). `boat.glb` is lit in the browser because it turns relative to the sun.
- `scripts/asset_pipeline.py`: content-hashed CSS, JS and 3D bundles, so a deployment can never pair new HTML with stale code.
- `content/film.json` and `scripts/film.py`: portfolio film chapters, transcript, excerpts and WebVTT captions.
- `SOURCES.md`: source provenance and editorial decisions.

## Build and check

```sh
npm run world                      # only after editing src/world
python3 scripts/build.py
python3 scripts/check.py
python3 scripts/test_i18n.py
node --check app.js
node --test scripts/test_film.cjs
python3 scripts/check_film.py
python3 scripts/package.py
```

Build and check scripts use only the Python standard library. Generated HTML is committed alongside its sources so the repository can be served without a build step. `PORTFOLIO_ALLOW_MISSING=1 python3 scripts/build.py` is a development build that leaves untranslated strings in English; the normal build refuses them.

`package.py` creates a clean `dist/` containing only public files. The existing hosting integration deploys changes pushed to `main`. After a deployment, verify the actual domain:

```sh
python3 scripts/check_live.py https://www.shengbojiang.me/
```

## Rebuilding an island

Requires Blender 5.x (tested with 5.3) and `cwebp`.

```sh
blender -b -P studio/run.py -- phoenix views    # five preview angles into studio/out/
studio/produce.sh phoenix                       # hero still, light bake, export, WebP packaging
python3 scripts/build.py                        # refreshes the asset version in every page
```

One sun and one sky are shared by every island (`kit.setup_world`), so islands are never rotated after baking. Static geometry is merged and unwrapped into one 4096-pixel atlas, lit with Cycles, and shipped at 2048 and 1024 pixels. Objects tagged with `animate()` stay separate so the site can move them; glass and light beams keep their own translucent material. The first Cycles run on a machine compiles its kernels and can take several minutes.

## The voyage

- The stage is `position: sticky` inside a tall section, so ordinary page scrolling drives the boat. Nothing intercepts the wheel or touch gestures. Anchors (`#stop-phoenix`), the stop rail, the previous and next buttons, and the island labels all jump to a stop.
- Between stops the camera follows the boat and a one-line caption explains how the next project relates to the last. At a stop the camera frames the island and a card links to the case study. The last stop rises to a chart of the route; on tall screens the chart turns upright.
- The sea is one shader: a half-resolution depth pass of the scene gives exact shorelines and foam, and the boat leaves a wake. The boat trims its sail with the Sailbot team's baseline rule (sail angle = 44/90 of the apparent wind angle).
- Rendering stops when the stage is off screen or the tab is hidden. Device pixel ratio is capped at 2 (1.5 on small or low-power devices, which also use the 1024-pixel atlases and skip the depth pass). If the first seconds are slow, resolution drops once.
- `prefers-reduced-motion` shows the illustrated sequence with a button to start the 3D voyage. Case-study islands then render single frames only when turned.
- A sea-sound toggle synthesises quiet noise in the browser; it is off by default and no audio file is downloaded.
- Append `?debug` to expose `window.__voyage.step(seconds)` / `window.__viewer.step(seconds)`, which advance the scene without `requestAnimationFrame`. This is how frames were checked in a background browser tab.

## Pages

- Home: the voyage, then a short introduction, four project cards and a contact line.
- Work: eight projects with Product, Research and Teams filters; filter state is reflected in the URL.
- Eight case studies: the interactive island with four captions, the question, key figures, the story, an engineering section, a plain list of what the work does not show, original media, links to related projects, sources, and previous/next stops in sailing order.
- Film: the two-minute portfolio video with chapters, transcript, download and captions in every site language. Sailbot and Sign-Translator pages include excerpts.
- About, Contact and a custom 404 page.

## Languages

English is at `/`. The other editions are Simplified Chinese (`/zh-hans/`), Traditional Chinese (`/zh-hant/`), Japanese (`/ja/`), Korean (`/ko/`), Hindi (`/hi/`), Spanish (`/es/`), French (`/fr/`), German (`/de/`) and Arabic (`/ar/`). Each has all twelve content pages and a translated 404 document. Visitors choose a language explicitly; there is no location-based redirect or external translation widget. The header selector links to the equivalent page and keeps query parameters and fragments.

Typography uses native Chinese, Japanese and Korean font stacks and upright emphasis for those scripts; Arabic uses self-hosted Noto Sans Arabic and Noto Naskh Arabic with right-to-left layout while the 3D stage, email addresses and numerals stay left-to-right; Hindi uses self-hosted Noto Devanagari faces. The 3D models contain numerals and symbols only, never words, so they need no translation.

Translations are machine-assisted and have not received a professional native-speaker review in every language. Original screenshots, diagrams, video, transcript and résumé retain their source language. No translation service is contacted during builds or visits.

## Caching

Generated pages reference `/assets/portfolio.<hash>.css`, `/assets/portfolio.<hash>.js` and `/assets/world.<hash>.js`, all served as immutable. 3D models, atlases and stills carry a `?v=<content hash>` query written by the build, so they can also be cached for a year. `scripts/check.py` rejects unversioned or mismatched bundle references. Keep previously generated hashed bundles available for browsers holding older HTML.

## Verification record

See the final section of `SOURCES.md` for what was and was not checked for the November 2026 redesign.

The older design/specification files and original `images/` remain as historical material; they are excluded from `dist/`.
