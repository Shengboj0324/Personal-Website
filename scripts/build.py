#!/usr/bin/env python3
"""Render the portfolio as portable, progressively enhanced static HTML.

The home page is a voyage: a sticky 3D stage that scroll drives from a home harbor
past one island per project. Without WebGL or JavaScript the same markup reads as
an illustrated sequence. Case studies open with the project's island.
"""
import json
from hashlib import sha256
from html import escape
from pathlib import Path
from asset_pipeline import browser_bundles
from i18n import LANGUAGES, ORIGIN, render_editions
from film import film_body, project_film, write_captions

ROOT = Path(__file__).resolve().parent.parent
BUNDLES = browser_bundles(ROOT)
CSS_URL = '/' + next(name for name in BUNDLES if name.endswith('.css'))
JS_URL = '/' + next(name for name in BUNDLES if '/portfolio.' in name and name.endswith('.js'))
WORLD_URL = '/' + next(name for name in BUNDLES if '/world.' in name)
PROJECTS = json.loads((ROOT / 'content/projects.json').read_text())
BY_SLUG = {p['slug']: p for p in PROJECTS}
VOYAGE = json.loads((ROOT / 'content/voyage.json').read_text())
ROUTE = [BY_SLUG[slug] for slug in VOYAGE['order']]
EMAIL = 'shengbojmicheal8866@gmail.com'
SOCIAL = [('GitHub', 'https://github.com/Shengboj0324'), ('Hugging Face', 'https://huggingface.co/Micheal324'), ('Kaggle', 'https://www.kaggle.com/michealjiang'), ('LinkedIn', 'https://www.linkedin.com/in/shengbo-jiang-16a03b334')]
SHORT = {
    'releaf': 'Releaf', 'phoenix': 'Urban heat', 'assay-planner': 'Assay Planner',
    'college-advisor': 'College Advisor', 'sign-translator': 'Language in motion',
    'igem': 'Science, clearly told', 'sailbot': 'Sailbot', 'developer-agent': 'Developer Agent',
}
E = escape
ARROW = '<span aria-hidden="true">→</span>'
OUT = '<span aria-hidden="true">↗</span>'
COMPASS = '<svg class="brand-mark" viewBox="0 0 40 40" width="40" height="40" aria-hidden="true"><circle cx="20" cy="20" r="18.5" fill="none" stroke="currentColor" stroke-width="1"/><path d="M20 5.5 23.2 20 20 34.5 16.8 20Z" fill="currentColor"/><path d="M5.5 20 20 16.8 34.5 20 20 23.2Z" fill="none" stroke="currentColor" stroke-width="1"/><circle cx="20" cy="20" r="1.6" fill="var(--paper)"/></svg>'


def version(path):
    """Short content hash so replaced 3D assets are never served stale."""
    return sha256((ROOT / path.lstrip('/')).read_bytes()).hexdigest()[:10]


def asset(path):
    return f'{path}?v={version(path)}'


def world_asset(slug):
    radius = VOYAGE['radius'].get(slug, 5.2)
    item = {'glb': asset(f'/assets/world/{slug}.glb'), 'tex': asset(f'/assets/world/{slug}.webp'), 'r': radius}
    if (ROOT / f'assets/world/{slug}-1k.webp').exists():
        item['tex1k'] = asset(f'/assets/world/{slug}-1k.webp')
    return item


def data_script(attribute, payload):
    return f'<script type="application/json" {attribute}>{json.dumps(payload, separators=(",", ":")).replace("<", chr(92) + "u003c")}</script>'


def external(label, url, class_name='text-link'):
    return f'<a class="{class_name}" href="{E(url, quote=True)}" target="_blank" rel="noopener noreferrer">{E(label)} {OUT}</a>'


def still(slug, alt='', size='card', eager=False, class_name='island-still'):
    width, height = (960, 720) if size == 'card' else (1800, 1350)
    return f'<img class="{class_name}" src="{asset(f"/assets/world/{slug}-{size}.webp")}" width="{width}" height="{height}" alt="{E(alt, quote=True)}"{" fetchpriority=\"high\"" if eager else " loading=\"lazy\""}>'


def island_alt(p):
    return f'A hand-built island model for {p["title"]}'


def card(p, index):
    return f'''<article class="project-card" data-category="{E(p['category'])}"><a class="card-image" href="/work/{p['slug']}/" aria-label="Explore {E(p['title'])}">{still(p['slug'], island_alt(p))}<span class="card-arrow" aria-hidden="true">↗</span></a><div class="card-meta"><span>{index:02d} / {E(p['category'])}</span><span>{E(p['year'])}</span></div><h3><a href="/work/{p['slug']}/">{E(p['title'])}</a></h3><p>{E(p['summary'])}</p></article>'''


def header(active):
    links = ''.join(f'<a href="{path}"{(" aria-current=\"page\"" if name == active else "")}>{name}</a>' for name, path in [('Work', '/work/'), ('Film', '/film/'), ('About', '/about/'), ('Contact', '/contact/')])
    return f'<a class="skip-link" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="/" aria-label="Shengbo Jiang, home">{COMPASS}<span>Shengbo Jiang</span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">Menu <span aria-hidden="true">+</span></button><nav id="primary-nav" aria-label="Main navigation">{links}<a class="resume-link" href="/assets/shengbo-jiang-resume.pdf" target="_blank" rel="noopener">Résumé <span aria-hidden="true">↗</span></a></nav></header>'


def footer():
    return f'''<footer class="site-footer"><div class="footer-top"><a class="footer-name" href="/">{COMPASS}<span>Shengbo Jiang<small>Curiosity, put to work.</small></span></a><nav class="footer-nav" aria-label="Footer"><a href="/#stop-harbor">The voyage</a><a href="/work/">Work</a><a href="/film/">Film</a><a href="/about/">About</a><a href="/contact/">Contact</a></nav><div class="footer-social">{''.join(external(n, u) for n, u in SOCIAL[:3])}</div></div><div class="footer-base"><span class="copyright">© 2026 · Palo Alto, CA</span><span class="footer-note">Islands modelled and lit in Blender. Built without a framework.</span></div></footer>'''


def document(title, description, body, active='', page_class='', world=False, image='/assets/social-cover.png'):
    world_tag = f'<link rel="modulepreload" href="{WORLD_URL}"><script type="module" src="{WORLD_URL}"></script>' if world else ''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)} — Shengbo Jiang</title>
<meta name="description" content="{E(description, quote=True)}">
<meta name="theme-color" content="#f7f2e7"><meta name="color-scheme" content="light">
<meta property="og:title" content="{E(title, quote=True)} — Shengbo Jiang"><meta property="og:description" content="{E(description, quote=True)}"><meta property="og:type" content="website"><meta property="og:image" content="{ORIGIN}{image}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{CSS_URL}"><script src="{JS_URL}" defer></script>{world_tag}
</head><body class="{page_class}">{header(active)}<main id="main">{body}</main>{footer()}</body></html>'''


def write(path, html):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


# ------------------------------------------------------------------ voyage
def voyage_layout():
    """World positions: islands run west to east, weaving nearer and farther."""
    spacing, weave = VOYAGE['spacing'], VOYAGE['weave']
    stops = []
    names = ['harbor'] + VOYAGE['order']
    for index, slug in enumerate(names):
        radius = VOYAGE['radius'].get(slug, 5.2)
        x, z = index * spacing, weave[index % len(weave)]
        # The boat waits just off each island's west shore, in frame beside it, then leaves around the front.
        mooring = VOYAGE['mooring'].get(slug, [round(-1.28 * radius, 2), round(0.52 * radius, 2)])
        stops.append({'id': slug, 'slug': slug, 'x': x, 'z': z, 'r': radius, 'mx': x + mooring[0], 'mz': z + mooring[1],
                      'wx': round(x + 0.6 * radius, 2), 'wz': round(z + radius + 6.5, 2)})
    end = stops[-1]
    stops.append({'id': 'chart', 'slug': None, 'x': end['x'], 'z': end['z'], 'r': 0, 'mx': end['wx'] + 26, 'mz': end['wz'] + 2})
    return stops


def voyage():
    stops = voyage_layout()
    count = len(ROUTE)
    payload = {'stops': stops, 'assets': {s['slug']: world_asset(s['slug']) for s in stops if s['slug']}, 'boat': asset('/assets/world/boat.glb')}
    intro = VOYAGE['intro']
    first = ROUTE[0]
    cards = [f'''<article class="stop stop-intro" data-stop id="stop-harbor">{still('harbor', 'The home harbor: a lighthouse, a boathouse and a pier', 'hero', True, 'stop-still')}<div class="stop-card">
<p class="eyebrow"><span class="status-dot"></span>STUDENT, DEVELOPER &amp; RESEARCHER <span class="eyebrow-place">PALO ALTO, CALIFORNIA</span></p>
<h1><span>Making intelligence</span><br><em>an instrument of discovery</em></h1>
<p class="stop-lede">{E(intro['lede'])}</p>
<div class="stop-actions"><a class="btn" href="#stop-{first['slug']}">Begin the voyage <span aria-hidden="true">↓</span></a><a class="text-link" href="/film/">Watch my portfolio film <span aria-hidden="true">▶</span></a></div>
<p class="stop-aside">{E(intro['aside'])}</p></div></article>''']
    for index, p in enumerate(ROUTE, 1):
        following = f'#stop-{ROUTE[index]["slug"]}' if index < count else '#stop-chart'
        cards.append(f'''<article class="stop" data-stop id="stop-{p['slug']}">{still(p['slug'], island_alt(p), 'card', False, 'stop-still')}<div class="stop-card">
<p class="stop-kicker"><span class="stop-number">{index:02d}<i>/ {count:02d}</i></span><span>{E(p['category'])}</span><span>{E(p['year'])}</span></p>
<h2>{E(p['title'])}</h2>
<p class="stop-lede">{E(p['tour'])}</p>
<div class="stop-actions"><a class="btn" href="/work/{p['slug']}/">Step ashore {ARROW}</a><a class="text-link" href="{following}">{'Next island' if index < count else 'See the whole chart'} <span aria-hidden="true">↓</span></a></div></div></article>''')
    chart = VOYAGE['chart']
    cards.append(f'''<article class="stop stop-chart" data-stop id="stop-chart"><div class="stop-card">
<p class="eyebrow">THE WHOLE CHART</p>
<h2>{chart['heading']}</h2>
<p class="stop-lede">{E(chart['lede'])}</p>
<div class="stop-actions"><a class="btn" href="/work/">Browse all eight projects {ARROW}</a><a class="text-link" href="/about/">About me {OUT}</a><a class="text-link" href="/contact/">Get in touch {OUT}</a></div></div></article>''')
    bridges = ''.join(f'<p class="bridge" data-bridge><span class="bridge-leg">LEG {i + 1:02d}</span><span>{E(text)}</span></p>' for i, text in enumerate([intro['bridge']] + [p['bridge'] for p in ROUTE]))
    labels = '<a class="voyage-label" data-label="0" href="#stop-harbor"><b>00</b><span>Home harbor</span></a>' + ''.join(
        f'<a class="voyage-label" data-label="{i}" href="#stop-{p["slug"]}"><b>{i:02d}</b><span>{E(SHORT[p["slug"]])}</span></a>' for i, p in enumerate(ROUTE, 1))
    rail = '<a data-rail="0" href="#stop-harbor" aria-label="Home harbor"><span>Home harbor</span></a>' + ''.join(
        f'<a data-rail="{i}" href="#stop-{p["slug"]}" aria-label="Stop {i}: {E(p["title"], quote=True)}"><span>{E(SHORT[p["slug"]])}</span></a>' for i, p in enumerate(ROUTE, 1)) + f'<a data-rail="{count + 1}" href="#stop-chart" aria-label="The whole chart"><span>The whole chart</span></a>'
    return f'''<section class="voyage" data-voyage style="--stops:{len(stops)}" aria-label="A voyage through eight projects">
<div class="voyage-stage"><canvas class="voyage-canvas" aria-hidden="true"></canvas><div class="voyage-vignette" aria-hidden="true"></div>
<div class="voyage-stops">{''.join(cards)}</div>
<div class="voyage-bridges" aria-hidden="true">{bridges}</div>
<div class="voyage-labels">{labels}</div>
<nav class="voyage-rail" aria-label="Stops on the voyage">{rail}</nav>
<div class="voyage-controls"><a class="voyage-step" data-step="-1" href="#stop-harbor" aria-label="Previous stop">←</a><a class="voyage-step" data-step="1" href="#stop-{first['slug']}" aria-label="Next stop">→</a><button class="voyage-sound" type="button" data-sound aria-pressed="false" hidden><span class="sound-on">Sea sound on</span><span class="sound-off">Sea sound off</span></button><a class="voyage-skip" href="#after-voyage">Skip the voyage <span aria-hidden="true">↓</span></a></div>
<p class="voyage-hint" aria-hidden="true"><span></span>Scroll to sail</p>
<button class="btn voyage-enable" type="button" data-voyage-enable hidden>Start the 3D voyage</button>
<div class="voyage-loader" aria-hidden="true"><span class="voyage-loader-bar"></span></div>
{data_script('data-voyage-data', payload)}</div></section>'''


def home():
    return document('Curiosity, put to work', 'I’m Shengbo Jiang, a student, developer, and researcher in Palo Alto. Sail through my work in sustainability, scientific computing, and accessible technology.', f'''{voyage()}
<section class="home-about shell" id="after-voyage"><span class="eyebrow">THE PERSON BEHIND THE PROJECTS</span><div><h2>I like the space between<br><em>“what if”</em> and <em>“it works.”</em></h2><p>I’m a student at Kehillah in Palo Alto. My projects move between environmental questions, machine learning, and the practical work of making something people can use.</p><a class="text-link" href="/about/">A little more about me {OUT}</a></div></section>
<section class="selected-section shell"><div class="section-heading"><div><span class="eyebrow">PREFER A LIST?</span><h2>Different questions.<br>A shared <em>curiosity.</em></h2></div><a class="text-link" href="/work/">All projects {OUT}</a></div><div class="project-grid home-grid">{''.join(card(p, i + 1) for i, p in enumerate([PROJECTS[i] for i in [0, 2, 1, 4]]))}</div></section>
<section class="contact-strip shell"><p>Have a question or an idea?</p><a href="/contact/">Let’s compare notes. {OUT}</a></section>''', page_class='home', world=True, image='/assets/social-cover.png')


def work():
    cards = ''.join(card(p, i + 1) for i, p in enumerate(PROJECTS))
    return document('Work', 'Projects in sustainability, scientific machine learning, accessibility, and software. Explore the questions, contributions, and evidence behind each one.', f'''<section class="page-intro shell"><span class="eyebrow">AN INDEX OF QUESTIONS &amp; EXPERIMENTS</span><h1>Curiosity,<br><em>put to work.</em></h1><div class="intro-bottom"><p>Products, research, and things built with a team.<br>Each one started with something I wanted to understand.</p><a class="btn ghost" href="/#stop-harbor">Sail through them instead {ARROW}</a></div></section><section class="work-section shell"><div class="filter-bar" hidden><div class="filters" role="group" aria-label="Filter projects">{''.join(f'<button type="button" data-filter="{x}" aria-pressed="{str(x=="All").lower()}">{x}</button>' for x in ['All','Product','Research','Teams'])}</div><span id="filter-count" role="status" aria-live="polite">8 projects</span></div><div class="project-grid">{cards}</div></section><section class="contact-strip shell"><p>The source is part of the story.</p><div class="profile-links">{external('GitHub',SOCIAL[0][1])}{external('Hugging Face',SOCIAL[1][1])}{external('Kaggle',SOCIAL[2][1])}</div></section>''', 'Work')


# ------------------------------------------------------------------ case studies
def island_stage(p):
    notes = ''.join(f'<li><button type="button" class="island-note" data-note="{i}"><span class="note-number">{i}</span><span class="note-body"><strong>{E(title)}</strong><span>{E(text)}</span></span></button></li>' for i, (title, text) in enumerate(p['hotspots'], 1))
    markers = ''.join(f'<button type="button" class="island-marker" data-marker="{i}" aria-pressed="false" aria-label="Point {i}: {E(title, quote=True)}" hidden>{i}</button>' for i, (title, _) in enumerate(p['hotspots'], 1))
    return f'''<section class="island-stage shell" data-island aria-labelledby="island-heading">
<div class="island-frame">{still(p['slug'], island_alt(p), 'hero', True, 'island-poster')}<canvas class="island-canvas" tabindex="0" aria-label="Interactive island model. Drag, or use the left and right arrow keys, to turn it."></canvas>{markers}<p class="island-hint" aria-hidden="true">Drag to turn the island</p><button type="button" class="island-reset" data-reset>Reset view</button></div>
<div class="island-guide"><span class="eyebrow">THE ISLAND, EXPLAINED</span><h2 id="island-heading">{E(p['island'])}</h2><ol class="island-notes">{notes}</ol><p class="media-caption">An illustration built for this site in Blender. It explains the idea; it is not data from the project.</p></div>
{data_script('data-island-data', world_asset(p['slug']))}</section>'''


def technical_section(p):
    technical = p.get('technical')
    if not technical:
        return ''
    modules = ''.join(
        f'<li><span class="technical-number">{index:02d}</span>'
        f'<h3>{E(title)}</h3><p>{E(description)}</p></li>'
        for index, (title, description) in enumerate(technical['modules'], 1)
    )
    source = external(*technical['source']) if technical.get('source') else ''
    return f'''<section class="technical-section shell" aria-labelledby="technical-heading">
<div class="technical-heading"><span class="eyebrow">INSIDE THE ENGINEERING</span><h2 id="technical-heading">{E(technical['heading'])}</h2></div>
<ol class="technical-grid">{modules}</ol>
<div class="technical-footnote"><p>{E(technical['footnote'])}</p>{source}</div></section>'''


def limits_section(p):
    if not p.get('limits'):
        return ''
    items = ''.join(f'<li>{E(text)}</li>' for text in p['limits'])
    return f'''<section class="limits-section shell" aria-labelledby="limits-heading"><span class="eyebrow">WHAT THIS DOES NOT SHOW</span><div><h2 id="limits-heading">The honest edges.</h2><ul class="limits">{items}</ul></div></section>'''


def connections_section(p):
    if not p.get('connections'):
        return ''
    links = ''.join(f'<a class="connection" href="/work/{slug}/">{still(slug, "", "card", False, "connection-still")}<span class="connection-body"><strong>{E(BY_SLUG[slug]["title"])}</strong><span>{E(text)}</span></span><span class="connection-arrow" aria-hidden="true">→</span></a>' for slug, text in p['connections'])
    return f'''<section class="connections-section shell" aria-labelledby="connections-heading"><div class="section-heading"><div><span class="eyebrow">NEARBY ISLANDS</span><h2 id="connections-heading">Where this connects.</h2></div></div><div class="connections">{links}</div></section>'''


def research_diagram(filename, alt, title, caption, height):
    return f'''<figure class="research-diagram">
<a class="diagram-image" href="/assets/{filename}" target="_blank" rel="noopener" aria-label="Open {E(title, quote=True)} diagram full size"><img src="/assets/{filename}" width="1040" height="{height}" loading="lazy" alt="{E(alt, quote=True)}"></a>
<figcaption><h3>{E(title)}</h3><p>{E(caption)}</p><a class="text-link" href="/assets/{filename}" target="_blank" rel="noopener">View full-size diagram {OUT}</a></figcaption></figure>'''


def sign_research_media():
    diagrams = [
        ('sign-architecture.svg', 'System diagram separating the runnable synthetic baseline from broader language, motion, and rendering research modules', 'The system, and its boundaries.', 'The repository’s architecture map separates the runnable synthetic core from the larger translation design. The newer continuous-motion experiments described above follow a separate training path.', 680),
        ('sign-manifold.svg', 'Language and motion encoders project paired examples into a shared normalized embedding space, trained with a contrastive objective', 'Can language and movement meet?', 'A spatiotemporal graph network encodes joint motion. Language and motion vectors are normalized and aligned with a symmetric contrastive loss: matching pairs should be closer than mismatched ones. Retrieval tests probe that alignment.', 480),
    ]
    primary = ''.join(research_diagram(*diagram) for diagram in diagrams)
    diffusion = research_diagram('sign-diffusion.svg', 'Conditional diffusion design: noise is progressively denoised into motion under language conditioning', 'A generative hypothesis.', 'This diagram documents the conditional-diffusion research design. The continuous experiments exposed a near-static failure mode; the selected continuous decoder instead uses discrete motion codes.', 470)
    streaming = research_diagram('sign-streaming.svg', 'Streaming design separating buffer, speech recognition, planning, motion generation, and rendering stages', 'The timing is part of the interface.', 'The streaming contract distinguishes time to the first output from sustained throughput. It also specifies an append-only committed prefix so a later prediction cannot rewrite motion already shown. This is a design contract, not a measured production-latency claim.', 430)
    return f'''<section class="research-notebook shell" aria-labelledby="notebook-heading">
<div class="section-heading"><div><span class="eyebrow">VISUAL NOTES / FROM THE REPOSITORY</span><h2 id="notebook-heading">From words<br>to <em>movement.</em></h2></div></div>
<figure class="rig-study"><img src="/assets/sign-hand-articulated.png" width="800" height="800" loading="lazy" alt="Original rendered hand-articulation test from the Sign-Translator avatar rig"><figcaption><span class="eyebrow">THE RENDERING LAYER</span><h3>A pose is only<br>the beginning.</h3><p>A motion model eventually has to drive a body. This original hand-articulation render comes from the repository’s rig checks: a close look at the geometry and joint behavior behind an avatar.</p><p class="media-caption">Static rig test. It does not depict a translated sentence.</p></figcaption></figure>
<div class="notebook-diagrams">{primary}</div>
<div class="diagram-details"><details><summary><span>Further exploration</span>How conditional diffusion was designed</summary>{diffusion}</details><details><summary><span>Further exploration</span>What streaming motion requires</summary>{streaming}</details></div>
</section>'''


def project_media(p):
    if p.get('video'):
        return f'''<section class="project-media shell"><div class="section-heading"><div><span class="eyebrow">THE PROJECT, IN MOTION</span><h2>A closer look.</h2></div>{external('Watch on YouTube','https://www.youtube.com/watch?v='+p['video'])}</div><div class="video-player"><video controls playsinline preload="none" poster="/assets/assay-cover.webp" aria-label="ZenithSync Assay Planner project demonstration"><source src="/assets/assay-demo.mp4" type="video/mp4"><a href="/assets/assay-demo.mp4">Download the project film</a></video></div><p class="media-caption">Original project walkthrough with synthetic narration. Recorded during the review stage. <a class="text-link" href="/assets/assay-transcript.txt" target="_blank" rel="noopener">Read the transcript ↗</a></p><figure class="evidence-figure"><img src="/assets/assay-demo.webp" width="625" height="1062" loading="lazy" alt="Actual Assay Planner output: selected treatment and control wells, response estimates, and downloadable plan"><figcaption><span class="eyebrow">FROM THE WORKING INTERFACE</span><h3>A plan you can inspect.</h3><p>The local interface lists selected wells, their roles, and the model’s response estimates. The result can be downloaded for further inspection.</p><p class="media-caption">Project screenshot from the public research repository.</p></figcaption></figure></section>'''
    if p['slug'] == 'college-advisor':
        return '<section class="architecture shell"><span class="eyebrow">SIMPLIFIED SYSTEM ARCHITECTURE</span><h2>Follow the evidence.</h2><ol class="pipeline"><li><span>01</span><strong>Question</strong><p>Student context and a specific information need.</p></li><li><span>02</span><strong>Retrieve</strong><p>Search across five source collections, weighting authoritative domains.</p></li><li><span>03</span><strong>Validate</strong><p>Specialized handling and cite-or-abstain checks.</p></li><li><span>04</span><strong>Respond</strong><p>An answer formatted with supporting citations.</p></li></ol></section>'
    if p['slug'] == 'sign-translator':
        return sign_research_media()
    if p['slug'] == 'releaf':
        return '<section class="project-media shell"><figure class="evidence-figure"><img src="/assets/releaf.webp" width="700" height="1443" loading="lazy" alt="Releaf’s community screen, showing shared reuse ideas"><figcaption><span class="eyebrow">FROM THE APP</span><h3>A feed of small, real actions.</h3><p>The community screen from an earlier release: reuse ideas shared by people using the app. The same screenshot is on the phone that stands on the island above.</p><p class="media-caption">Actual app screenshot. Later builds reorganise the tabs around Create, Impact and Community.</p></figcaption></figure></section>'
    if p['slug'] == 'igem':
        return '<section class="project-media shell"><figure class="wide-figure"><img src="/assets/igem.webp" width="1600" height="809" loading="lazy" alt="LCG-China iGEM 2024 project banner"><figcaption class="media-caption">The team’s 2024 project banner, from the public wiki.</figcaption></figure></section>'
    return ''


def project(p):
    position = VOYAGE['order'].index(p['slug'])
    count = len(ROUTE)
    facts = ''.join(f'<div><strong>{E(value)}</strong><span>{E(label)}</span></div>' for value, label in p['facts'])
    sections = ''.join(f'<section class="story-section"><span class="story-number">{j + 1:02d}</span><div><h2>{E(heading)}</h2><p>{E(text)}</p></div></section>' for j, (heading, text) in enumerate(p['sections']))
    nxt = ROUTE[(position + 1) % count]
    prv = ROUTE[(position - 1) % count]
    links = ''.join(external(n, u) for n, u in p['links'])
    return document(p['title'], p['summary'], f'''<section class="case-header shell"><a class="back-link" href="/work/">← All work</a><div class="case-kicker"><span>{E(p['category'])} / {E(p['year'])}</span><a href="/#stop-{p['slug']}">STOP {position + 1:02d} OF {count:02d} ON THE VOYAGE</a></div><h1>{E(p['title'])}</h1><p class="case-subtitle">{E(p['subtitle'])}</p><div class="case-meta"><div><span>ROLE</span><p>{E(p['role'])}</p></div><div><span>CONTEXT</span><p>{E(p['organization'])}</p></div><div><span>TOOLS &amp; METHODS</span><p>{E(' · '.join(p['tools']))}</p></div></div></section>
{island_stage(p)}
<section class="case-intro shell"><span class="eyebrow">THE QUESTION</span><p>{E(p['intro'])}</p></section>
{f'<section class="case-facts shell" aria-label="Project figures">{facts}</section>' if facts else ''}
<div class="case-story shell">{sections}</div>
{technical_section(p)}{limits_section(p)}{project_film(p['slug'])}{project_media(p)}{connections_section(p)}
<section class="case-sources shell"><span class="eyebrow">CONTEXT &amp; FURTHER READING</span><div><p>{E(p['note'])}</p><div class="source-links">{links}</div></div></section>
<nav class="case-nav shell" aria-label="More projects"><a class="case-nav-link" href="/work/{prv['slug']}/"><span class="eyebrow">PREVIOUS STOP</span><strong>{E(prv['title'])}</strong></a><a class="case-nav-link next" href="/work/{nxt['slug']}/"><span class="eyebrow">NEXT STOP</span><strong>{E(nxt['title'])}</strong><span class="next-arrow" aria-hidden="true">→</span></a></nav>''', 'Work', 'case-page', world=True, image=f'/assets/world/{p["slug"]}-card.webp')


# ------------------------------------------------------------------ about, contact
def about():
    experiences = [('2026', 'Pioneer Academics', 'Student researcher', 'Studied how surface heat and neighborhood vulnerability change priorities for cooling interventions in Phoenix.', 'phoenix'), ('2025–2026', 'Athena AI Labs', 'Software developer intern', 'Built across a SwiftUI app, Python API, and retrieval system for college advising.', 'college-advisor'), ('2024–present', 'Rematter Cooperation', 'Cofounder & software engineer', 'Developed Releaf and its supporting backend and AI services.', 'releaf'), ('2024–present', 'Science Seed Project', 'Founder & developer', 'Built a science-learning platform with courses, videos, student and teacher accounts, quizzes, and translation workflows. Sign-language technology is a separate research effort.', 'sign-translator'), ('2025–2026', 'Kehillah Sailbot', 'Software contributor', 'Contributed navigation, steering, wind filtering, state estimation, and physics-simulation improvements.', 'sailbot'), ('2024', 'LCG-China · iGEM', 'Wiki & entrepreneurship team lead', 'Led the website presentation and ExploreAid business plan for a Gold Medal team.', 'igem'), ('2023–2025', 'Hamden Hall', 'Carbon Footprint Club technical lead · Math Team leader', 'Built carbon-tracking web applications and databases, coordinated student contributors, and led math contest practice.', None)]
    timeline = ''.join(f'<article class="timeline-row"><span>{E(date)}</span><div><h3>{E(name)}</h3><span class="role">{E(role)}</span></div><p>{E(desc)}{f" <a class=\"timeline-link\" href=\"/work/{slug}/\">Visit the island {ARROW}</a>" if slug else ""}</p></article>' for date, name, role, desc, slug in experiences)
    return document('About', 'I’m Shengbo Jiang, a student at Kehillah in Palo Alto, building across sustainability, scientific computing, and accessible education.', f'''<section class="about-hero shell"><div><span class="eyebrow">A LITTLE ABOUT ME</span><h1>Hello,<br>I’m <em>Shengbo.</em></h1><p class="about-lede">A student who likes turning an unfamiliar question into something I can explore, test, and build.</p><p>I’m based in Palo Alto and attend Kehillah Jewish High School, with graduation expected in 2027. Before that, I studied at Hamden Hall in Connecticut.</p><div class="about-tags"><span>SOFTWARE</span><span>SCIENCE</span><span>SUSTAINABILITY</span></div></div><figure class="portrait"><img src="/assets/portrait.webp" width="472" height="910" alt="Shengbo Jiang at an event" fetchpriority="high"><figcaption><span>Shengbo Jiang</span><span>Palo Alto, CA ↗</span></figcaption></figure></section><section class="about-statement shell"><span class="eyebrow">HOW I APPROACH THE WORK</span><div><h2>Start with a question.<br><em>Stay for the details.</em></h2><p>My work moves between applications people interact with and research tools that help investigate a question. Releaf puts sustainability into a daily routine. My Phoenix research asks what a heat map leaves out. The assay planner studies how an experiment might use its measurements more carefully.</p><p>I’m interested in the decisions that connect those layers: how data is organized, what an interface makes understandable, and how to tell whether a result supports the claim being made.</p></div></section><figure class="about-harbor shell">{still('harbor', 'The home harbor from the voyage: a lighthouse, a boathouse and a pier', 'hero', False, 'wide-still')}<figcaption class="media-caption">The home harbor, where the voyage on the front page begins. <a class="text-link" href="/#stop-harbor">Set sail {ARROW}</a></figcaption></figure><section class="experience shell"><div class="section-heading"><div><span class="eyebrow">PLACES I’VE LEARNED &amp; CONTRIBUTED</span><h2>A few chapters.</h2></div><a class="text-link" href="/assets/shengbo-jiang-resume.pdf" download>Download résumé <span aria-hidden="true">↓</span></a></div>{timeline}</section><section class="about-details shell"><div><span class="eyebrow">THE TOOLBOX</span><h2>What I work with.</h2><p>Python, Swift, Java, JavaScript, TypeScript, SQL</p><p>SwiftUI, Django, FastAPI, React / Next.js, PostgreSQL, Git, Docker</p></div><div><span class="eyebrow">SELECTED RECOGNITION</span><ul class="honors"><li><strong>iGEM Gold Medal</strong><span>LCG-China team · 2024</span></li><li><strong>Top-two team placement</strong><span>China High School Social Innovation Competition and Incubation Camp · 2025</span></li><li><strong>Highest Scorer</strong><span>Greater New Haven League · 2024</span></li></ul></div></section><section class="contact-strip shell"><p>There’s always another good question.</p><a href="/contact/">Let’s talk. {OUT}</a></section>''', 'About')


def contact():
    social = ''.join(f'<a class="contact-profile" href="{u}" target="_blank" rel="noopener noreferrer"><span>0{i+1}</span><strong>{n}</strong><span aria-hidden="true">↗</span></a>' for i, (n, u) in enumerate(SOCIAL))
    return document('Contact', 'Get in touch with Shengbo Jiang about software, research, sustainability, and potential collaborations.', f'''<section class="contact-hero shell"><span class="eyebrow">A CONVERSATION IS A GOOD PLACE TO START</span><h1>What are you<br><em>curious about?</em></h1><p>A project, a research question, or something you think I’d find interesting—I’d be glad to hear about it.</p><div class="email-block"><span class="eyebrow">WRITE TO ME</span><a class="email-address" href="mailto:{EMAIL}">{EMAIL} <span aria-hidden="true">↗</span></a><button class="copy-email" type="button" data-copy="{EMAIL}" hidden>Copy email address</button><span class="copy-status" role="status" aria-live="polite"></span></div></section><section class="contact-bottom shell"><div><span class="eyebrow">ELSEWHERE ON THE INTERNET</span><h2>Follow the work.</h2><p>Source code, model documentation,<br>and experiments in progress.</p></div><div>{social}</div></section>''', 'Contact')


def main():
    for name, data in BUNDLES.items():
        (ROOT / name).write_bytes(data)
    slugs = [p['slug'] for p in PROJECTS]
    if len(slugs) != len(set(slugs)) or sorted(slugs) != sorted(VOYAGE['order']):
        raise ValueError('Project slugs must be unique and match the voyage order')
    (ROOT / 'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#17302c"/><path d="M32 9 37 32 32 55 27 32Z" fill="#f7f2e7"/><path d="M9 32 32 27 55 32 32 37Z" fill="none" stroke="#f0785a" stroke-width="2.4"/><circle cx="32" cy="32" r="2.6" fill="#17302c"/></svg>')
    pages = {'/': home(), '/work/': work(), '/about/': about(), '/contact/': contact(), '/film/': document('Portfolio film', 'Watch Shengbo Jiang’s portfolio film with chapters, project demonstrations, and multilingual captions.', film_body(), 'Film', 'film-page')}
    pages.update({f'/work/{p["slug"]}/': project(p) for p in PROJECTS})
    pages['/404.html'] = document('Page not found', 'This page could not be found. Explore Shengbo Jiang’s portfolio.', f'<section class="page-intro shell lost"><span class="eyebrow">404 / OFF THE CHART</span><h1>Let’s find<br><em>our way back.</em></h1><p>This page isn’t here. The projects are a good place to start.</p><div class="stop-actions"><a class="btn" href="/">Return to the harbor {ARROW}</a><a class="text-link" href="/work/">Explore the work {OUT}</a></div></section>')
    for path, html in render_editions(pages):
        write(Path(path), html)
    write_captions()
    print(f'Rendered {len(pages) * len(LANGUAGES)} static pages across {len(LANGUAGES)} languages.')


if __name__ == '__main__':
    main()
