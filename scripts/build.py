#!/usr/bin/env python3
"""Render the portfolio as portable, progressively enhanced static HTML."""
import json
from html import escape
from pathlib import Path
from asset_pipeline import browser_bundles

ROOT = Path(__file__).resolve().parent.parent
BUNDLES = browser_bundles(ROOT)
CSS_URL = '/' + next(name for name in BUNDLES if name.endswith('.css'))
JS_URL = '/' + next(name for name in BUNDLES if name.endswith('.js'))
PROJECTS = json.loads((ROOT / 'content/projects.json').read_text())
EMAIL = 'shengbojmicheal8866@gmail.com'
SOCIAL = [('GitHub', 'https://github.com/Shengboj0324'), ('Hugging Face', 'https://huggingface.co/Micheal324'), ('Kaggle', 'https://www.kaggle.com/michealjiang'), ('LinkedIn', 'https://www.linkedin.com/in/shengbo-jiang-16a03b334')]
E = escape


def external(label, url, class_name='text-link'):
    return f'<a class="{class_name}" href="{E(url, quote=True)}" target="_blank" rel="noopener noreferrer">{E(label)} <span aria-hidden="true">↗</span></a>'


def art_svg():
    lines = []
    for i in range(48):
        angle = i * 180 / 48
        lines.append(f'<ellipse cx="280" cy="280" rx="205" ry="85" transform="rotate({angle} 280 280)"/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 560" fill="none"><g stroke="#315344" stroke-width=".85">' + ''.join(lines) + '</g><circle cx="280" cy="280" r="24" fill="#c96540"/><circle cx="280" cy="280" r="8" fill="#edece3"/></svg>'


def visual(p, detail=False):
    slug = p['slug']
    if slug == 'releaf':
        return '<div class="project-art art-releaf"><span class="art-word" aria-hidden="true">releaf.</span><span class="art-annotation">A little change, every day.</span><div class="phone"><img src="/assets/releaf.webp" width="700" height="1443" alt="Releaf’s community screen, showing shared reuse ideas" loading="lazy"></div><span class="art-bottom">RETHINK. REUSE. RELEAF.</span></div>'
    if slug == 'phoenix':
        cells = ''.join(f'<i class="{"shared" if i < 17 else "different"}"></i>' for i in range(37))
        return f'<div class="project-art art-phoenix"><span class="art-annotation">PHOENIX, ARIZONA / 2026</span><div class="heat-orbit" aria-hidden="true"></div><div class="heat-number">17<span>of 37</span></div><div class="tract-dots" aria-hidden="true">{cells}</div><span class="art-bottom">Same city. Different priorities.</span></div>'
    if slug == 'assay-planner':
        return '<div class="project-art art-assay"><img src="/assets/assay-cover.webp" width="560" height="280" alt="ZenithSync assay-design project illustration with treatment wells and response curves" loading="lazy"><span class="art-bottom">ZENITHSYNC / EXPERIMENTAL DESIGN</span></div>'
    if slug == 'college-advisor':
        return '<div class="project-art art-advisor"><span class="art-annotation">COLLEGEADVISOR / RAG</span><div class="citation-stack" aria-hidden="true"><div class="citation-paper paper-back">01 / Find the evidence</div><div class="citation-paper paper-front"><span class="quote-mark">“</span><strong>Good answers<br>start with<br><em>good sources.</em></strong><span class="paper-rule"></span><small>RETRIEVE → CHECK → CITE</small></div></div><span class="art-bottom">A source behind every answer.</span></div>'
    if slug == 'sign-translator':
        return '<div class="project-art art-sign"><span class="art-annotation">LANGUAGE ↔ MOTION</span><svg viewBox="0 0 600 370" fill="none" aria-hidden="true"><g stroke="currentColor" stroke-width="2"><path d="M195 300L240 235L265 165L300 145L335 165L360 235L405 300M265 165L220 195L183 145L164 100M335 165L380 195L417 145L436 100M300 145V105M265 165L275 240H325L335 165M275 240L255 330M325 240L345 330"/><circle cx="300" cy="75" r="30"/><path d="M164 100L140 68M164 100L155 56M164 100L174 58M164 100L189 77M436 100L460 68M436 100L445 56M436 100L426 58M436 100L411 77"/></g><g fill="currentColor">'+''.join(f'<circle cx="{x}" cy="{y}" r="5"/>' for x,y in [(240,235),(265,165),(335,165),(360,235),(220,195),(380,195),(183,145),(417,145),(164,100),(436,100),(275,240),(325,240)])+'</g></svg><span class="art-bottom">A study of language, structure & movement.</span></div>'
    if slug == 'igem':
        return '<div class="project-art art-igem"><img src="/assets/igem.webp" width="1600" height="809" alt="LCG-China iGEM 2024 project banner" loading="lazy"><span class="art-bottom">WIKI & ENTREPRENEURSHIP / IGEM 2024</span></div>'
    if slug == 'sailbot':
        return '<div class="project-art art-sail"><span class="art-annotation">KEHILLAH SAILBOT / CONTROL & SIMULATION</span><svg viewBox="0 0 600 380" fill="none" aria-hidden="true"><g stroke="currentColor" stroke-width="1.5"><path d="M306 55V290H181L306 55ZM320 95L410 275H320V95ZM160 304H435L402 330H196Z"/><path d="M60 351Q105 328 150 351T240 351T330 351T420 351T510 351"/><path stroke-dasharray="5 8" d="M70 180C150 70 160 260 255 90"/></g></svg><span class="art-bottom">Finding a heading in changing conditions.</span></div>'
    return '<div class="project-art art-agent"><span class="art-annotation">ZENITHSYNC / DEVELOPER AGENT</span><div class="agent-type" aria-hidden="true">{<span>test.<br>learn.<br>repeat.</span>}</div><span class="art-bottom">Better experiments. Inspectable results.</span></div>'


def card(p, index):
    return f'<article class="project-card" data-category="{E(p["category"])}"><a class="card-image" href="/work/{p["slug"]}/" aria-label="Explore {E(p["title"])}">{visual(p)}<span class="card-arrow" aria-hidden="true">↗</span></a><div class="card-meta"><span>{index:02d} / {E(p["category"])}</span><span>{E(p["year"])}</span></div><h3><a href="/work/{p["slug"]}/">{E(p["title"])}</a></h3><p>{E(p["summary"])}</p></article>'


def header(active):
    links = ''.join(f'<a href="{path}"{(" aria-current=\"page\"" if name == active else "")}>{name}</a>' for name,path in [('Work','/work/'),('About','/about/'),('Contact','/contact/')])
    return f'<a class="skip-link" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="/" aria-label="Shengbo Jiang, home"><span class="brand-mark" aria-hidden="true">sj.</span><span>Shengbo Jiang</span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">Menu <span aria-hidden="true">+</span></button><nav id="primary-nav" aria-label="Main navigation">{links}<a class="resume-link" href="/assets/shengbo-jiang-resume.pdf" target="_blank" rel="noopener">Résumé <span aria-hidden="true">↗</span></a></nav></header>'


def footer():
    return '<footer class="site-footer"><a class="footer-name" href="/">Shengbo Jiang<span>Curiosity, put to work.</span></a><div class="footer-social">'+''.join(external(n,u) for n,u in SOCIAL[:3])+'</div><span class="copyright">© 2026 · Palo Alto, CA</span></footer>'


def document(title, description, body, active='', page_class=''):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} — Shengbo Jiang</title>
<meta name="description" content="{E(description, quote=True)}">
<meta name="theme-color" content="#f4f2eb"><meta name="color-scheme" content="light">
<meta property="og:title" content="{E(title, quote=True)} — Shengbo Jiang"><meta property="og:description" content="{E(description, quote=True)}"><meta property="og:type" content="website"><meta property="og:image" content="/assets/social-cover.png">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{CSS_URL}"><script src="{JS_URL}" defer></script>
</head><body class="{page_class}">{header(active)}<main id="main">{body}</main>{footer()}</body></html>'''


def write(path, html):
    target=ROOT/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(html)


def home():
    chosen = [PROJECTS[i] for i in [0,2,1,3]]
    cards=''.join(card(p, i+1) for i,p in enumerate(chosen))
    return document('Curiosity, put to work', 'I’m Shengbo Jiang, a student, developer, and researcher in Palo Alto. Explore my work in sustainability, scientific computing, and accessible technology.', f'''
<section class="home-hero shell">
<div class="hero-eyebrow"><span class="status-dot"></span> STUDENT, DEVELOPER & RESEARCHER <span class="hero-location">PALO ALTO, CALIFORNIA</span></div>
<div class="hero-composition"><div class="hero-copy"><h1>Good questions.<br><em>Useful things.</em></h1><p>I’m Shengbo. I build software and study how it can help us understand the world—and do a little more for it.</p><a class="round-link" href="/work/">Explore my work <span aria-hidden="true">↗</span></a></div><figure class="hero-art"><img src="/assets/curiosity.svg" width="560" height="560" alt=""><figcaption>IDEAS TAKE SHAPE.</figcaption><span class="art-coordinate" aria-hidden="true">FIG. 01 / CURIOSITY</span></figure></div>
<div class="hero-foot"><span>From everyday sustainability to scientific questions.</span><a href="#selected-work">A few things I’ve been working on <span aria-hidden="true">↓</span></a></div></section>
<section class="selected-section shell" id="selected-work"><div class="section-heading"><div><span class="eyebrow">01 / SELECTED WORK</span><h2>Different questions.<br>A shared <em>curiosity.</em></h2></div><a class="text-link" href="/work/">All projects <span aria-hidden="true">↗</span></a></div><div class="project-grid home-grid">{cards}</div></section>
<section class="home-about shell"><span class="eyebrow">02 / THE PERSON BEHIND THE PROJECTS</span><div><h2>I like the space between<br><em>“what if”</em> and <em>“it works.”</em></h2><p>I’m a student at Kehillah in Palo Alto. My projects move between environmental questions, machine learning, and the practical work of making something people can use.</p><a class="text-link" href="/about/">A little more about me <span aria-hidden="true">↗</span></a></div></section>
<section class="contact-strip shell"><p>Have a question or an idea?</p><a href="/contact/">Let’s compare notes. <span aria-hidden="true">↗</span></a></section>''', page_class='home')


def work():
    cards=''.join(card(p,i+1) for i,p in enumerate(PROJECTS))
    return document('Work', 'Projects in sustainability, scientific machine learning, accessibility, and software. Explore the questions, contributions, and evidence behind each one.', f'''<section class="page-intro shell"><span class="eyebrow">AN INDEX OF QUESTIONS & EXPERIMENTS</span><h1>Curiosity,<br><em>put to work.</em></h1><div class="intro-bottom"><p>Products, research, and things built with a team.<br>Each one started with something I wanted to understand.</p><span class="index-count">01 — 08</span></div></section><section class="work-section shell"><div class="filter-bar" hidden><div class="filters" role="group" aria-label="Filter projects">{''.join(f'<button type="button" data-filter="{x}" aria-pressed="{str(x=="All").lower()}">{x}</button>' for x in ['All','Product','Research','Teams'])}</div><span id="filter-count" role="status" aria-live="polite">8 projects</span></div><div class="project-grid">{cards}</div></section><section class="contact-strip shell"><p>The source is part of the story.</p><div class="profile-links">{external('GitHub',SOCIAL[0][1])}{external('Hugging Face',SOCIAL[1][1])}{external('Kaggle',SOCIAL[2][1])}</div></section>''', 'Work')


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


def research_diagram(filename, alt, title, caption, height):
    return f'''<figure class="research-diagram">
<a class="diagram-image" href="/assets/{filename}" target="_blank" rel="noopener" aria-label="Open {E(title, quote=True)} diagram full size"><img src="/assets/{filename}" width="1040" height="{height}" loading="lazy" alt="{E(alt, quote=True)}"></a>
<figcaption><h3>{E(title)}</h3><p>{E(caption)}</p><a class="text-link" href="/assets/{filename}" target="_blank" rel="noopener">View full-size diagram <span aria-hidden="true">↗</span></a></figcaption></figure>'''


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
<figure class="rig-study"><img src="/assets/sign-hand-articulated.png" width="800" height="800" loading="lazy" alt="Original rendered hand-articulation test from the Sign-Translator avatar rig"><figcaption><span class="eyebrow">01 / THE RENDERING LAYER</span><h3>A pose is only<br>the beginning.</h3><p>A motion model eventually has to drive a body. This original hand-articulation render comes from the repository’s rig checks: a close look at the geometry and joint behavior behind an avatar.</p><p class="media-caption">Static rig test. It does not depict a translated sentence.</p></figcaption></figure>
<div class="notebook-diagrams">{primary}</div>
<div class="diagram-details"><details><summary><span>Further exploration</span>How conditional diffusion was designed</summary>{diffusion}</details><details><summary><span>Further exploration</span>What streaming motion requires</summary>{streaming}</details></div>
</section>'''


def project(p, i):
    facts=''.join(f'<div><strong>{E(value)}</strong><span>{E(label)}</span></div>' for value,label in p['facts'])
    sections=''.join(f'<section class="story-section"><span class="story-number">0{j+1}</span><div><h2>{E(heading)}</h2><p>{E(text)}</p></div></section>' for j,(heading,text) in enumerate(p['sections']))
    media=''
    if p.get('video'):
        media=f'''<section class="project-media shell"><div class="section-heading"><div><span class="eyebrow">THE PROJECT, IN MOTION</span><h2>A closer look.</h2></div>{external('Watch on YouTube','https://www.youtube.com/watch?v='+p['video'])}</div><div class="video-player"><video controls playsinline preload="none" poster="/assets/assay-cover.webp" aria-label="ZenithSync Assay Planner project demonstration"><source src="/assets/assay-demo.mp4" type="video/mp4"><a href="/assets/assay-demo.mp4">Download the project film</a></video></div><p class="media-caption">Original project walkthrough with synthetic narration. Recorded during the review stage. <a class="text-link" href="/assets/assay-transcript.txt" target="_blank" rel="noopener">Read the transcript ↗</a></p><figure class="evidence-figure"><img src="/assets/assay-demo.webp" width="625" height="1062" loading="lazy" alt="Actual Assay Planner output: selected treatment and control wells, response estimates, and downloadable plan"><figcaption><span class="eyebrow">FROM THE WORKING INTERFACE</span><h3>A plan you can inspect.</h3><p>The local interface lists selected wells, their roles, and the model’s response estimates. The result can be downloaded for further inspection.</p><p class="media-caption">Project screenshot from the public research repository.</p></figcaption></figure></section>'''
    elif p['slug']=='college-advisor':
        media='<section class="architecture shell"><span class="eyebrow">SIMPLIFIED SYSTEM ARCHITECTURE</span><h2>Follow the evidence.</h2><ol class="pipeline"><li><span>01</span><strong>Question</strong><p>Student context and a specific information need.</p></li><li><span>02</span><strong>Retrieve</strong><p>Keyword and vector search across source collections.</p></li><li><span>03</span><strong>Validate</strong><p>Specialized handling and cite-or-abstain checks.</p></li><li><span>04</span><strong>Respond</strong><p>An answer formatted with supporting citations.</p></li></ol></section>'
    elif p['slug']=='sign-translator':
        media=sign_research_media()
    nxt=PROJECTS[(i+1)%len(PROJECTS)]
    links=''.join(external(n,u) for n,u in p['links'])
    return document(p['title'],p['summary'],f'''<section class="case-header shell"><a class="back-link" href="/work/">← All work</a><div class="case-kicker"><span>{E(p['category'])} / {E(p['year'])}</span><span>PROJECT {i+1:02d}</span></div><h1>{E(p['title'])}</h1><p class="case-subtitle">{E(p['subtitle'])}</p><div class="case-meta"><div><span>ROLE</span><p>{E(p['role'])}</p></div><div><span>CONTEXT</span><p>{E(p['organization'])}</p></div><div><span>TOOLS & METHODS</span><p>{E(' · '.join(p['tools']))}</p></div></div></section><div class="case-cover shell">{visual(p,True)}</div><section class="case-intro shell"><span class="eyebrow">THE QUESTION</span><p>{E(p['intro'])}</p></section>{f'<section class="case-facts shell" aria-label="Project figures">{facts}</section>' if facts else ''}<div class="case-story shell">{sections}</div>{technical_section(p)}{media}<section class="case-sources shell"><span class="eyebrow">CONTEXT & FURTHER READING</span><div><p>{E(p['note'])}</p><div class="source-links">{links}</div></div></section><a class="next-project shell" href="/work/{nxt['slug']}/"><span class="eyebrow">NEXT PROJECT</span><strong>{E(nxt['title'])}</strong><span class="next-arrow" aria-hidden="true">↗</span></a>''','Work','case-page')


def about():
    experiences=[('2026','Pioneer Academics','Student researcher','Studied how surface heat and neighborhood vulnerability change priorities for cooling interventions in Phoenix.'),('2025–2026','Athena AI Labs','Software developer intern','Built across a SwiftUI app, Python API, and retrieval system for college advising.'),('2024–present','Rematter Cooperation','Cofounder & software engineer','Developed Releaf and its supporting backend and AI services.'),('2024–present','Science Seed Project','Founder & developer','Built a science-learning platform with courses, videos, student and teacher accounts, quizzes, and translation workflows. Sign-language technology is a separate research effort.'),('2025–2026','Kehillah Sailbot','Software contributor','Contributed navigation, steering, wind filtering, state estimation, and physics-simulation improvements.'),('2024','LCG-China · iGEM','Wiki & entrepreneurship team lead','Led the website presentation and ExploreAid business plan for a Gold Medal team.'),('2023–2025','Hamden Hall','Carbon Footprint Club technical lead · Math Team leader','Built carbon-tracking web applications and databases, coordinated student contributors, and led math contest practice.')]
    timeline=''.join(f'<article class="timeline-row"><span>{E(date)}</span><div><h3>{E(name)}</h3><span class="role">{E(role)}</span></div><p>{E(desc)}</p></article>' for date,name,role,desc in experiences)
    return document('About','I’m Shengbo Jiang, a student at Kehillah in Palo Alto, building across sustainability, scientific computing, and accessible education.',f'''<section class="about-hero shell"><div><span class="eyebrow">A LITTLE ABOUT ME</span><h1>Hello,<br>I’m <em>Shengbo.</em></h1><p class="about-lede">A student who likes turning an unfamiliar question into something I can explore, test, and build.</p><p>I’m based in Palo Alto and attend Kehillah Jewish High School, with graduation expected in 2027. Before that, I studied at Hamden Hall in Connecticut.</p><div class="about-tags"><span>SOFTWARE</span><span>SCIENCE</span><span>SUSTAINABILITY</span></div></div><figure class="portrait"><img src="/assets/portrait.webp" width="472" height="910" alt="Shengbo Jiang at an event" fetchpriority="high"><figcaption><span>Shengbo Jiang</span><span>Palo Alto, CA ↗</span></figcaption></figure></section><section class="about-statement shell"><span class="eyebrow">HOW I APPROACH THE WORK</span><div><h2>Start with a question.<br><em>Stay for the details.</em></h2><p>My work moves between applications people interact with and research tools that help investigate a question. Releaf puts sustainability into a daily routine. My Phoenix research asks what a heat map leaves out. The assay planner studies how an experiment might use its measurements more carefully.</p><p>I’m interested in the decisions that connect those layers: how data is organized, what an interface makes understandable, and how to tell whether a result supports the claim being made.</p></div></section><section class="experience shell"><div class="section-heading"><div><span class="eyebrow">PLACES I’VE LEARNED & CONTRIBUTED</span><h2>A few chapters.</h2></div><a class="text-link" href="/assets/shengbo-jiang-resume.pdf" download>Download résumé <span aria-hidden="true">↓</span></a></div>{timeline}</section><section class="about-details shell"><div><span class="eyebrow">THE TOOLBOX</span><h2>What I work with.</h2><p>Python, Swift, Java, JavaScript, TypeScript, SQL</p><p>SwiftUI, Django, FastAPI, React / Next.js, PostgreSQL, Git, Docker</p></div><div><span class="eyebrow">SELECTED RECOGNITION</span><ul class="honors"><li><strong>iGEM Gold Medal</strong><span>LCG-China team · 2024</span></li><li><strong>Top-two team placement</strong><span>China High School Social Innovation Competition and Incubation Camp · 2025</span></li><li><strong>Highest Scorer</strong><span>Greater New Haven League · 2024</span></li></ul></div></section><section class="contact-strip shell"><p>There’s always another good question.</p><a href="/contact/">Let’s talk. <span aria-hidden="true">↗</span></a></section>''','About')


def contact():
    social=''.join(f'<a class="contact-profile" href="{u}" target="_blank" rel="noopener noreferrer"><span>0{i+1}</span><strong>{n}</strong><span aria-hidden="true">↗</span></a>' for i,(n,u) in enumerate(SOCIAL))
    return document('Contact','Get in touch with Shengbo Jiang about software, research, sustainability, and potential collaborations.',f'''<section class="contact-hero shell"><span class="eyebrow">A CONVERSATION IS A GOOD PLACE TO START</span><h1>What are you<br><em>curious about?</em></h1><p>A project, a research question, or something you think I’d find interesting—I’d be glad to hear about it.</p><div class="email-block"><span class="eyebrow">WRITE TO ME</span><a class="email-address" href="mailto:{EMAIL}">{EMAIL} <span aria-hidden="true">↗</span></a><button class="copy-email" type="button" data-copy="{EMAIL}" hidden>Copy email address</button><span class="copy-status" role="status" aria-live="polite"></span></div></section><section class="contact-bottom shell"><div><span class="eyebrow">ELSEWHERE ON THE INTERNET</span><h2>Follow the work.</h2><p>Source code, model documentation,<br>and experiments in progress.</p></div><div>{social}</div></section>''','Contact')


def main():
    for name, data in BUNDLES.items():
        (ROOT / name).write_bytes(data)
    slugs=[p['slug'] for p in PROJECTS]
    if len(slugs)!=len(set(slugs)):
        raise ValueError('Project slugs must be unique')
    (ROOT/'assets/curiosity.svg').write_text(art_svg())
    (ROOT/'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#254b3d"/><text x="13" y="43" font-family="Georgia,serif" font-size="38" fill="#f4f2eb">sj.</text></svg>')
    write(Path('index.html'),home())
    write(Path('work/index.html'),work())
    write(Path('about/index.html'),about())
    write(Path('contact/index.html'),contact())
    for i,p in enumerate(PROJECTS):write(Path('work')/p['slug']/'index.html',project(p,i))
    write(Path('404.html'),document('Page not found','This page could not be found. Explore Shengbo Jiang’s portfolio.', '<section class="page-intro shell"><span class="eyebrow">404 / A SMALL DETOUR</span><h1>Let’s find<br><em>our way back.</em></h1><p>This page isn’t here. The projects are a good place to start.</p><a class="round-link" href="/work/">Explore the work <span aria-hidden="true">↗</span></a></section>'))
    print(f'Rendered {len(PROJECTS)+5} static pages.')

if __name__=='__main__':main()
