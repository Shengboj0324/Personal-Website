# Island dioramas — art direction

The portfolio's home page is a sea voyage. A small autonomous sailboat carries the
visitor from a home harbor to eight islands, one per project. Each island is a
hand-built miniature that explains the project at a glance, lit once in Cycles and
baked to a texture so it runs smoothly in the browser. The same model is also
rendered as stills for the case-study pages.

The quality bar is a collector's miniature: a visitor should want to lean in and
look around. `islands/harbor.py` is the reference for density, proportion and tone.
Render it (`preview`) before you start, and match or beat it.

## Look
- **Toy-scale clay.** Chunky, rounded, slightly exaggerated proportions. Everything
  has a bevel. Nothing is razor thin: minimum thickness about 0.03.
- **Readable silhouette.** One or two tall hero pieces (1.8 to 4.5 units high), a
  middle layer of props, and a ground layer of small detail. The island should read
  from the default camera (front-left, above) and still hold up from behind.
- **Tell the truth about the project.** Every hero object stands for something real
  in the project brief. Counts that the brief gives (8 doses, 9 tools, 5 collections)
  must be exact. Do not invent data, results or logos.
- **No words.** The site ships in ten languages. Numerals and symbols are fine;
  English words, labels and brand logos are not.
- **Density.** 60 to 140 objects. Fill the ground with purposeful small things
  (stones, tufts, cables, crates, flowers) but leave walking room so it does not
  look cluttered. Vary heights and rotate props a few degrees off-axis.
- **Colour.** Each island has its own palette (given in your brief) plus the shared
  neutrals in `kit.py`. Use 5 to 7 hues, with one accent that appears three or more
  times. Keep large surfaces light and matte; put saturated colour on small parts.
- **Glow.** Use emissive materials (`mat(color, emit=3..6)`) for a few lamps, screens
  or highlighted elements. They are baked in and can pulse on the site.

## Geometry rules
- Island top is z = 0, sea surface is z = `WATER_Z` (-1.0). Keep within radius 6 of
  the origin and under 5 units tall. Start with `island_base(...)`; change `R`, `seed`,
  `lobes` and the colours so no two islands share an outline.
- The front of the island faces **-Y**. The sun comes from the front-right and is
  shared by every island, so never plan on rotating the island afterwards.
- Budget: **under 70,000 triangles** (`[kit] triangles:` is printed on every run).
  Use `verts=` 8 to 16 on small cylinders, `seg=` 10 to 16 on small spheres.
- Objects must touch what they stand on. No floating props (except clouds, orbiting
  or bobbing things), no z-fighting faces: offset coplanar surfaces by 0.01.
- Things sitting in the sea (buoys, posts) go around the rim, within radius 6.5.

## Motion and points of interest
- `animate(ob, kind, ...)` keeps an object separate so the site can move it. Tag 3 to
  7 objects per island: `spin` (axis, speed), `bob` (amp, speed), `sway` (amp, speed,
  axis), `pulse` (speed), `orbit` (speed; spins around the object's origin, so set
  the origin to the orbit centre with `set_origin`). Join multi-part movers with
  `join([...], name)` first, then `set_origin`, then `animate`.
- `hotspot(n, (x, y, z))` for n = 1 to 4: place each just above the object it explains.
  The site shows a numbered marker there with a caption.

## Working method
1. Read `kit.py` (helpers and their arguments) and `islands/harbor.py`.
2. Write `islands/<slug>.py` with a `build(mode)` function ending in `finish(slug, mode, ...)`.
   If you need a helper the kit lacks, define it in your own file. Do not edit `kit.py`,
   `run.py`, or another island.
3. Render and look: `/Applications/Blender.app/Contents/MacOS/Blender -b -P studio/run.py -- <slug> views 2>&1 | grep -E "\[kit\]|Error|Traceback|line "`
   writes `studio/out/<slug>_preview.png` plus `_back`, `_top`, `_low`, `_right`.
   Open every image and critique it honestly: composition, proportions, colour,
   floating or intersecting parts, empty areas, anything that reads as a mistake.
4. Iterate at least four rounds. Stop when the island is clearly at or above the
   harbor's standard from all five views.
5. Do not run `bake` or `hero`; those are run centrally afterwards.
