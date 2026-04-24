# Personal Portfolio Website Design System Brief

## Purpose

This document is written for Claude Code or another AI coding agent building Shengbo Jiang's personal portfolio website. The goal is not to clone Hack the North or Apple. The goal is to extract their strongest design patterns and adapt them into a polished, technical, student-founder portfolio that feels premium, credible, modern, and highly engineered.

The final website should combine:

1. Apple's discipline, spacing, visual hierarchy, restraint, typography, product-storytelling structure, and premium interaction feel.
2. Hack the North's rich narrative sections, playful layered visuals, animated assets, community energy, project storytelling, stats blocks, sponsor/logo grids, FAQ structure, and immersive scroll experience.

The result should feel like:

> Apple-level polish + Hack-the-North-level story energy + AI/ML research portfolio credibility.

Do not make the site look like a generic student resume page. Do not make it look like a plain Tailwind template. Do not overuse neon gradients, random glassmorphism, or meaningless animations. Every animation and visual element must support the story: Shengbo is a young technical builder working across AI, sustainability, accessibility, astrobiology, and computational biology.

---

# 1. Reference Website Analysis

## 1.1 Apple.com Design Pattern Analysis

Apple's homepage is structurally simple but visually disciplined. It relies on large product sections, concise copy, strong typography, generous spacing, full-width visual panels, and very clear calls to action.

### Observable content and structure

Apple's homepage uses a global top navigation with product/category links such as Store, Mac, iPad, iPhone, Watch, Vision, AirPods, TV & Home, Entertainment, Accessories, and Support. Under that, the page uses stacked product-marketing panels: for example, a Mother's Day hero, an iPhone section, a MacBook section, iPad Air, Apple Watch, AirPods, Apple Trade In, Apple Card, and an entertainment carousel/list area.

### What to extract for Shengbo's website

Use Apple's structure for high-trust portfolio storytelling:

- A thin, fixed, translucent global navigation bar.
- Large clean hero section with one primary identity statement.
- Wide sections that each focus on one major project or identity pillar.
- Minimal copy above the fold, with technical depth available through expandable sections and project pages.
- Clean two-button call-to-action pattern, such as `View Projects` and `Download Resume`.
- Strong product-style project panels, where each project is treated like a serious product rather than a school activity.
- High-resolution visuals, mockups, diagrams, cards, screenshots, and technical architecture illustrations.

### Apple-style layout rules

- Use large vertical sections with clear boundaries.
- Prefer centered headlines in hero/product sections.
- Keep primary headings short and confident.
- Use secondary text under the headline, not long paragraphs.
- Use one strong visual per section.
- Use heavy spacing instead of borders when possible.
- Use soft backgrounds: white, off-white, very light gray, deep black for dramatic sections.
- Use interaction sparingly: hover states, smooth reveals, carousels, sticky nav, scroll-based fade/scale.

### Apple-style typography rules

Use a clean system type stack:

```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", "Segoe UI", sans-serif;
```

Recommended scale:

```css
--font-hero: clamp(3.25rem, 8vw, 7.5rem);
--font-section-title: clamp(2.25rem, 5vw, 5rem);
--font-card-title: clamp(1.5rem, 2.5vw, 2.25rem);
--font-body-large: clamp(1.125rem, 1.6vw, 1.5rem);
--font-body: 1rem;
--font-small: 0.875rem;
```

Apple-style copy should be short, clean, and product-focused:

- "AI systems for sustainability, accessibility, and scientific discovery."
- "Locally trained models. Production software. Research-driven engineering."
- "Built across iOS, full-stack systems, RAG, multimodal AI, and computational biology."

Avoid noisy headings like:

- "Welcome to my portfolio!!!"
- "Here are all my amazing projects"
- "I am passionate about technology and want to change the world"

### Apple-style JavaScript behavior

Use JavaScript for polish, not chaos:

- Sticky global navigation with blur and transparency.
- Smooth anchor navigation.
- IntersectionObserver-based reveal animations.
- Minimal carousel for selected project visuals.
- Responsive mobile menu.
- Optional scroll progress indicator.
- Optional motion preference detection with `prefers-reduced-motion`.

Do not build animation-heavy logic that damages performance. The site should remain fast and readable without JavaScript where possible.

---

## 1.2 Hack the North Design Pattern Analysis

Hack the North's homepage is much more immersive and narrative-driven. It uses layered illustrated assets, firefly animations, themed backgrounds, stats blocks, project-story cards, speaker/judge carousels, sponsor grids, FAQ sections, and a highly event-like sense of momentum.

### Observable content and structure

The Hack the North page opens with a JavaScript-enabled experience and heavily uses image assets: fireflies, campfire, goose cart, rocks, crystals, foreground/midground/background layers, water, beams, sponsor art, and headshots. Its content includes a hero, welcome/community sections, stats blocks, project story showcases, judge/speaker sections, What's New sections, sponsor logos, FAQ, organizer note, and footer. It presents strong numerical credibility, including 1200+ hackers, 178 schools, 10 countries, 235 submitted projects, 650,000+ km travelled, 180+ mentors, and 15+ workshops.

### What to extract for Shengbo's website

Use Hack the North's storytelling model for portfolio depth:

- A visual world, not just flat cards.
- Section-specific background motifs.
- Animated small particles or subtle glowing elements to create energy.
- Strong stats section for credibility.
- Project story cards that include the problem, technical approach, shipped artifact, and impact.
- A "builder journey" section that moves from early software work to AI research and leadership.
- A logo/link grid for platforms, tools, technologies, organizations, and projects.
- A detailed FAQ section for recruiters, collaborators, judges, and admissions readers.

### Hack-the-North-style layout rules

- Use multiple themed sections with visual identity.
- Use decorative assets as background, not as random clutter.
- Layer foreground, midground, and background visuals with absolute positioning.
- Include stats as big numbers with compact labels.
- Include project/story carousels but keep the controls clean.
- Use playful details only in controlled areas.

### Adapted visual motif for Shengbo

Instead of geese, fireflies, rocks, and campsite art, use a technical-scientific motif:

- Floating data particles.
- Neural graph nodes.
- Orbit paths.
- Bacterial cellulose fiber patterns.
- Subtle sign-language hand-outline motion frames.
- Sustainability leaf/circuit hybrids.
- Spectral lines for astrobiology.
- Soft glass panels over dark space-like backgrounds.

The site can have a lightweight animated canvas/SVG background in selected sections, but it must not become a gimmick.

### Hack-the-North-style JavaScript behavior

Use JavaScript for:

- Particle field background in hero or selected dark sections.
- Parallax layers with very small movement.
- Project carousel or horizontal scroll panel.
- FAQ accordion.
- Stats count-up animation once visible.
- Project tabs or filters.
- Floating interactive cards.
- Hover-triggered micro animations.

Do not recreate Hack the North's exact illustrations, characters, or brand assets. Build an original scientific/AI visual system.

---

# 2. Final Design Direction for Shengbo's Website

## 2.1 Brand Positioning

The website should position Shengbo as:

> A young AI engineer and technical founder building production systems for sustainability, accessibility, and scientific discovery.

Core identity pillars:

1. AI engineering
2. Scientific machine learning
3. Sustainability technology
4. Accessibility technology
5. Computational biology and iGEM leadership
6. Full-stack product execution
7. Research-grade ambition with shipped-product discipline

Tone:

- Serious
- Technical
- Premium
- Clear
- Ambitious
- Precise
- Not childish
- Not generic
- Not over-polished in a fake way

The website must read like a founder/research-engineer portfolio, not a simple high school activity page.

---

# 3. Recommended Website Architecture

## 3.1 Navigation

Use a fixed top navigation bar inspired by Apple.

Desktop nav items:

- Home
- Work
- Projects
- Research
- Leadership
- Resume
- Contact

Right-side actions:

- GitHub
- LinkedIn
- Resume PDF

Mobile:

- Hamburger menu
- Full-screen overlay menu
- Smooth closing animation

Nav styling:

```css
.navbar {
  position: fixed;
  top: 0;
  width: 100%;
  backdrop-filter: saturate(180%) blur(18px);
  background: rgba(255,255,255,0.72);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  z-index: 1000;
}
```

For dark hero mode:

```css
.navbar.dark {
  background: rgba(5, 8, 14, 0.62);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  color: white;
}
```

---

## 3.2 Homepage Sections

### Section 1: Hero

Purpose: Immediately establish identity and credibility.

Suggested layout:

- Full viewport hero.
- Dark or near-black background with subtle animated particles, orbit lines, spectral lines, or neural graph nodes.
- Centered title.
- Short subtitle.
- Two CTAs.
- Small credibility row.

Recommended hero copy:

```text
Shengbo Jiang
AI Engineer · Technical Founder · Scientific ML Builder

I build AI systems for sustainability, accessibility, and scientific discovery — from locally trained multimodal models to production iOS and full-stack platforms.
```

CTA buttons:

- View Selected Work
- Download Resume

Credibility row:

- iGEM 2024 Gold Medalist, Tech Lead
- USACO Silver
- 5,000+ users across Releaf
- Open-source AI systems
- Full-stack + iOS + ML

Hero visual idea:

- A large animated technical constellation.
- Nodes labeled: Sustainability AI, Astrobio-gen, Sign Language AI, iGEM AMP Design, Athena AI Labs.
- Lines connect the nodes in a graph.
- On hover, show small preview cards.

Implementation suggestion:

Use SVG or Canvas for the background. Keep it lightweight.

Do not use massive video backgrounds unless optimized.

---

### Section 2: Featured Work Overview

Purpose: Give a high-level project grid.

Use Apple-style product cards with Hack-the-North-style storytelling energy.

Cards:

1. Releaf / Sustainability AI
2. Astrobio-gen
3. Sign Language Translation AI
4. Athena AI Labs College Advisory System
5. iGEM 2024 Bacterial Cellulose + AMP Platform
6. CarbonTrack Platform

Each card should include:

- Project name
- One-line outcome
- Technical stack tags
- Impact metric
- Link to details

Example card:

```text
Releaf — Sustainability AI Engine
Domain-specialized AI platform for recycling, upcycling, and environmental decision support.

Stack: iOS · RAG · GNN · Vision Model · Sustainability Knowledge Base
Impact: 5,000+ users worldwide
```

Design:

- 2-column grid on desktop.
- 1-column on mobile.
- Large rounded cards.
- Soft shadows.
- Hover lift.
- Subtle gradient overlays.
- Strong image/diagram area at the top of each card.

---

### Section 3: Metrics / Proof Section

Purpose: Replace vague self-praise with measurable proof.

Use Hack-the-North-style large stats.

Suggested stats:

```text
5,000+ users
Releaf global user reach

$2,000+ raised
Funding for Rematter / Releaf

Gold Medal
Tech Lead, iGEM 2024

USACO Silver
Competitive programming credential

2024–Present
Active open-source AI development

Full-stack + AI
iOS, backend, RAG, ML, web systems
```

Animation:

- Count-up numbers on first scroll into view.
- Fade/slide reveal.
- Disable animation if `prefers-reduced-motion` is enabled.

---

### Section 4: Deep Project Feature — Releaf / Sustainability AI

Purpose: This should be one of the strongest sections.

Recommended heading:

```text
Sustainability AI that turns environmental questions into actionable decisions.
```

Content blocks:

1. Problem
2. Model architecture
3. Product system
4. Impact
5. Future roadmap

Expanded content:

```text
Releaf is an iOS-based sustainability platform built through Rematter Cooperation. The system is designed to answer environmental questions with domain-specific grounding rather than generic chatbot responses. It combines mobile product design, AI reasoning, retrieval-augmented generation, visual understanding, and sustainability-specific knowledge workflows.
```

Technical architecture bullets:

- iOS frontend for user interaction and environmental Q&A.
- Backend APIs for model orchestration, request routing, logging, and analytics.
- RAG pipeline for retrieving sustainability-specific knowledge before generation.
- Vision model layer for interpreting user-uploaded images of materials, waste, packaging, or recyclable objects.
- Graph-based modeling direction for connecting materials, disposal pathways, charities, upcycling strategies, and local environmental actions.
- Prompt/response safety and instrumentation for iteration.
- Built with the goal of practical recommendations, not generic environmental slogans.

UI treatment:

- Use a light Apple-style product panel.
- Include an iPhone mockup showing Releaf screens.
- Add an architecture diagram: User Input → Vision/RAG → Sustainability AI Engine → Actionable Guidance → Feedback Loop.
- Use subtle green/blue gradients, but keep it premium.

Interactive idea:

- A mini demo card where the user selects a sample object, such as plastic bottle, old hoodie, cardboard package, broken electronics, or food container.
- The UI shows a mock sustainability reasoning chain:
  - Identify material
  - Determine reuse/recycle pathway
  - Suggest local action
  - Explain environmental benefit

Do not claim unsupported scientific accuracy. Use language like "designed to", "built to support", "prototype includes", or "roadmap includes" when necessary.

---

### Section 5: Deep Project Feature — Sign Language Translation AI

Recommended heading:

```text
Local multimodal AI for more accessible communication.
```

Expanded content:

```text
The Sign Language Translation project explores live translation from spoken/video input into sign-language-oriented output. The system was developed and trained locally, with emphasis on accessibility, privacy, and the challenge of translating continuous language rather than isolated alphabet-level recognition.
```

Technical content:

- Local training workflow rather than purely API-dependent translation.
- Video/speech input pipeline.
- Sign recognition and generation direction.
- Dataset preprocessing for hand/body landmarks, frame normalization, label mapping, and sequence modeling.
- Model direction: vision encoder + temporal sequence model + language alignment layer.
- Challenge: sentence-level sign language requires grammar, timing, facial expression, context, and motion continuity, not just letter classification.
- Product goal: help students and young people access complex educational content.

Suggested architecture diagram:

```text
Microphone / Video Input
        ↓
Speech Recognition / Visual Landmark Extraction
        ↓
Language Understanding Layer
        ↓
Sign Sequence Planner
        ↓
Avatar / Video / Symbolic Sign Output
        ↓
Human Feedback + Dataset Improvement
```

UI treatment:

- Use dark section with blue/purple technical gradients.
- Add animated hand landmark lines or skeleton nodes.
- Use a side-by-side demo layout:
  - Left: input sentence
  - Middle: model pipeline
  - Right: sign output preview panel

Important implementation note:

Do not overpromise that the project already performs professional-grade sign translation if that is not fully implemented. Present it as a serious, locally trained accessibility AI project with a clear roadmap and technical direction.

---

### Section 6: Deep Project Feature — Athena AI Labs Internship

Recommended heading:

```text
AI-driven college advisory infrastructure built as a full-stack decision system.
```

Expanded content:

```text
At Athena AI Labs, Shengbo works on an AI-driven college application advisory system that combines an iOS frontend, cloud-hosted backend, embedded admissions/program data, ChromaDB-backed retrieval, and profile-conditioned recommendation logic. The system is designed to support personalized guidance across universities, majors, programs, and summer opportunities.
```

Technical content:

- iOS application frontend for student-facing workflows.
- Cloud-hosted backend for user profiles, request handling, recommendation orchestration, and API integration.
- RAG pipeline backed by ChromaDB.
- Embedded admissions and program datasets.
- Profile-conditioned retrieval: recommendations change based on student academic interests, activities, constraints, and target fields.
- Recommendation outputs for universities, majors, programs, and summer opportunities.
- Potential evaluation direction: relevance scoring, user feedback, ranking quality, hallucination control, source-grounded output.

UI treatment:

- Apple-style professional SaaS dashboard mockup.
- Include cards for:
  - Student Profile
  - Retrieval Layer
  - Recommendation Engine
  - Program Match Output
  - Feedback Loop

Suggested microcopy:

```text
From static admissions data to profile-aware recommendations.
```

---

### Section 7: Deep Project Feature — iGEM Leadership

Recommended heading:

```text
Technical leadership across computational biology, software, and engineered biomaterials.
```

Expanded content:

```text
As Tech Lead for LCG-China's iGEM 2024 Gold Medal project, Shengbo led technical development across computational tools, web applications, documentation, and wet-lab support workflows. The project focused on antimicrobial peptide applications and a bioactive bacterial-cellulose dressing concept, connecting computational screening with engineered biomaterial design.
```

Technical content:

- Led technical development for software components supporting wet-lab and engineering workflows.
- Built sequence design/evaluation tools for antimicrobial peptide candidates.
- Integrated docking or structure prediction outputs into reporting and screening workflows.
- Supported data pipelines for AMP screening.
- Worked across interdisciplinary subteams.
- Contributed to documentation and technical communication.
- Project concept: bacterial-cellulose dressing functionalized with modular antimicrobial peptides, designed for medical/wound-care relevance.

Suggested section layout:

- Left: leadership narrative.
- Right: technical workflow diagram.

Workflow diagram:

```text
AMP Candidate Design
        ↓
Sequence Evaluation
        ↓
Structure / Docking Output Integration
        ↓
Screening Data Pipeline
        ↓
Bacterial Cellulose Functionalization Concept
        ↓
Technical Documentation + Competition Delivery
```

Visual motif:

- Microscopic fiber texture.
- Peptide chain linework.
- Soft biomedical colors: white, pale blue, soft cyan, muted green.

Do not use clinical claims that sound like a proven medical product unless validated. Use precise language such as "developed a project concept," "designed a prototype workflow," or "supported screening and reporting."

---

### Section 8: Astrobio-gen Feature

Recommended heading:

```text
Multimodal astrobiology AI for exoplanet habitability inference.
```

Content:

```text
Astrobio-gen is an open-source AI system exploring exoplanet habitability and biosignature likelihood mapping. The system is designed around multimodal fusion of planetary parameters, stellar activity, orbital data, spectral signals, and galactic-scale priors.
```

Technical content:

- Multimodal feature construction.
- NASA Exoplanet Archive/public catalog direction.
- Physical range validation.
- Missing value control.
- Feature standardization.
- Tensor construction for downstream scoring.
- Advanced attention and hierarchy learning.
- Uncertainty estimates.
- Galactic prior for habitability gradients.
- Targeted research submission direction.

Visual treatment:

- Dark space-like section.
- Orbital lines.
- Spectral bars.
- Floating exoplanet cards.
- Technical architecture panel.

---

### Section 9: Leadership Timeline

Purpose: Show progression and maturity.

Timeline entries:

- Hamden Hall Country Day School → Kehillah Jewish High School
- Carbon Footprint Club Tech Lead
- Math Team Leader
- Science Seed Project Founder
- iGEM 2024 Tech Lead and Gold Medalist
- Rematter Cooperation Cofounder and Tech Engineer
- Athena AI Labs Software Intern
- Astrobio-gen open-source development

Design:

- Vertical timeline on desktop.
- Collapsible cards on mobile.
- Each item includes role, date, organization, and technical outcome.

---

### Section 10: Technical Skills System

Avoid a boring list. Use grouped skill panels.

Groups:

#### AI / ML

- Multimodal modeling
- RAG systems
- Vision models
- Graph neural networks
- Parameter-efficient training
- Attention mechanisms
- Noise reduction
- Hierarchy learning
- Local model training
- Evaluation workflows

#### Full-stack / Product

- iOS development
- Web app development
- Backend APIs
- Database design
- ChromaDB
- RESTful APIs
- Git/GitHub
- Deployment workflows

#### Scientific / Research Domains

- Sustainability AI
- Computational biology
- Astrobiology AI
- Exoplanet habitability modeling
- Antimicrobial peptide workflows
- Accessibility AI

#### Leadership

- Technical roadmapping
- Cross-functional coordination
- Student contributor mentoring
- Competition delivery
- Product execution

Design:

- Use pill tags but with hierarchy.
- Add hover detail cards for major skills.
- Do not dump 100 badges without context.

---

### Section 11: FAQ

Use Hack-the-North-style FAQ accordion.

Recommended questions:

1. What kind of AI systems does Shengbo build?
2. What is the strongest project on this portfolio?
3. What is Releaf and what makes the Sustainability AI model different?
4. What is the Sign Language Translation project trying to solve?
5. What did Shengbo do as iGEM Tech Lead?
6. What did Shengbo build during the Athena AI Labs internship?
7. Is Astrobio-gen open source?
8. What technologies does Shengbo work with?
9. Is Shengbo available for internships, collaborations, or research work?
10. Where can I see code or contact him?

FAQ design:

- Accordion with smooth expand/collapse.
- Keep answers precise.
- Use subtle borders and no heavy boxes.

---

### Section 12: Footer

Footer content:

- Name
- One-line identity
- Email
- GitHub
- LinkedIn
- Resume
- Project links
- Copyright

Design:

- Dark footer.
- Subtle animated particles or grid.
- Clean link columns.

---

# 4. Visual Design System

## 4.1 Color Palette

Use a premium technical palette.

```css
:root {
  --color-bg: #f5f5f7;
  --color-surface: #ffffff;
  --color-text: #111827;
  --color-muted: #6b7280;
  --color-border: rgba(17, 24, 39, 0.10);

  --color-dark: #05070d;
  --color-dark-2: #0b1020;
  --color-dark-card: rgba(255, 255, 255, 0.06);

  --color-blue: #0071e3;
  --color-cyan: #38bdf8;
  --color-green: #22c55e;
  --color-purple: #8b5cf6;
  --color-amber: #f59e0b;
}
```

Usage:

- Apple-inspired white/light gray for general sections.
- Dark scientific panels for AI/research sections.
- Green/cyan only for sustainability/accessibility accents.
- Purple/blue for AI systems.
- Avoid rainbow gradients everywhere.

## 4.2 Backgrounds

Recommended backgrounds:

- Hero: dark gradient + particle graph.
- Releaf: light background + green/cyan accent gradient.
- Sign Language: dark navy + hand landmark line animation.
- iGEM: white/blue biomedical background with fiber texture.
- Astrobio-gen: black/space gradient + spectral/orbit overlays.
- Resume/skills: clean light cards.

## 4.3 Cards

Card style:

```css
.card {
  border-radius: 28px;
  background: rgba(255,255,255,0.84);
  border: 1px solid rgba(17,24,39,0.08);
  box-shadow: 0 24px 70px rgba(15,23,42,0.08);
  backdrop-filter: blur(18px);
}
```

Dark card:

```css
.dark-card {
  border-radius: 28px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 24px 80px rgba(0,0,0,0.35);
}
```

Hover:

```css
.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 32px 90px rgba(15,23,42,0.14);
}
```

Use hover effects only on clickable cards.

---

# 5. JavaScript / React Implementation Requirements

## 5.1 Recommended Stack

Use one of these:

### Option A: Next.js

Best for production portfolio.

- Next.js App Router
- TypeScript
- Tailwind CSS
- Framer Motion
- React Server Components where reasonable
- Static generation for content-heavy pages
- MDX for project writeups

### Option B: Vite + React

Simpler but still strong.

- Vite
- React
- TypeScript
- Tailwind CSS
- Framer Motion
- React Router if multi-page

Strong recommendation: Use Next.js + TypeScript.

## 5.2 Animation Library

Use Framer Motion for:

- Section reveal
- Card hover
- Hero text reveal
- FAQ accordion
- Project carousel transitions

Use plain CSS for:

- Button hover
- Background gradients
- Small decorative animations

Use Canvas/SVG only for:

- Particle field
- Technical node graph
- Orbit visual

Do not use five animation libraries. Keep the stack lean.

## 5.3 Core React Components

Build these reusable components:

```text
/components
  Navbar.tsx
  Hero.tsx
  SectionShell.tsx
  ProjectCard.tsx
  FeaturedProject.tsx
  MetricCard.tsx
  SkillPill.tsx
  Timeline.tsx
  FAQAccordion.tsx
  Footer.tsx
  TechnicalGraphBackground.tsx
  ProjectArchitectureDiagram.tsx
  CTAButton.tsx
```

## 5.4 Data-Driven Content

Do not hardcode every project directly inside JSX. Create a data file:

```text
/data/projects.ts
/data/skills.ts
/data/timeline.ts
/data/faqs.ts
```

Example:

```ts
export const projects = [
  {
    title: "Releaf — Sustainability AI Engine",
    category: "Sustainability AI",
    summary: "Domain-specialized AI platform for recycling, upcycling, and environmental decision support.",
    impact: "5,000+ users worldwide",
    stack: ["iOS", "RAG", "Vision Model", "GNN", "Backend APIs"],
    theme: "sustainability",
    href: "/projects/releaf"
  }
];
```

## 5.5 IntersectionObserver Reveal Hook

Use this for lightweight reveal if not using Framer Motion everywhere.

```ts
export function useInViewOnce<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [isVisible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.18 }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return { ref, isVisible };
}
```

## 5.6 Reduced Motion

Respect accessibility.

```ts
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
```

If reduced motion is enabled:

- Disable parallax.
- Disable particle movement.
- Disable count-up animation.
- Use instant section visibility.

## 5.7 Performance Requirements

Target:

- Lighthouse performance above 90.
- No massive unoptimized images.
- Use `next/image` for images in Next.js.
- Lazy-load below-fold heavy components.
- Avoid layout shift.
- Keep JS bundle lean.
- Canvas animation must pause when offscreen.
- Prefer CSS transforms over layout-changing animation.

---

# 6. Interaction Design Details

## 6.1 Hero Node Graph

Behavior:

- Nodes float slowly.
- Lines connect nodes.
- Hovering a node shows a project preview tooltip.
- Clicking scrolls to the project section.

Nodes:

- Sustainability AI
- Astrobio-gen
- Sign Language AI
- iGEM AMP Platform
- Athena Advisory System
- CarbonTrack

Design:

- Keep opacity low.
- Never cover text.
- Disable on small mobile screens or simplify into static SVG.

## 6.2 Project Cards

Behavior:

- Hover lift by 4 to 6 px.
- Subtle glow matching project theme.
- Arrow icon moves 4 px right.
- Card image scales to 1.03.

Do not rotate cards aggressively.

## 6.3 Stats Count-Up

Behavior:

- Count starts when stats section enters viewport.
- Duration: 900 to 1400 ms.
- Ease-out.

Example:

```text
0 → 5000+
0 → 2000+
Gold Medal fades in directly instead of counting.
```

## 6.4 FAQ Accordion

Behavior:

- One or multiple items can be open.
- Smooth height animation.
- Chevron rotates 180 degrees.
- Keyboard accessible.

## 6.5 Project Detail Pages

Each project should have a dedicated route:

```text
/projects/releaf
/projects/sign-language-ai
/projects/astrobio-gen
/projects/igem
/projects/athena-ai-labs
/projects/carbontrack
```

Each page should include:

- Hero
- Problem
- Technical architecture
- Implementation details
- Impact
- What I learned
- Future roadmap
- Links / screenshots / repo when available

---

# 7. Copywriting Style Guide

## 7.1 Voice

Use:

- Direct technical language.
- Clear project outcomes.
- Specific systems and architecture.
- Strong verbs: built, designed, led, implemented, shipped, architected, integrated, evaluated.

Avoid:

- Empty passion statements.
- Excessive adjectives.
- Fake humility.
- Unsupported claims.
- Long paragraphs that feel like college application essays.

## 7.2 Good Examples

```text
Built a sustainability-focused AI engine that combines mobile product workflows, retrieval-augmented generation, visual understanding, and environmental knowledge grounding.
```

```text
Led the technical workstream for an iGEM Gold Medal project, connecting antimicrobial peptide screening tools with documentation and wet-lab support workflows.
```

```text
Developed a locally trained accessibility AI project exploring video/speech-to-sign-language translation beyond alphabet-level recognition.
```

## 7.3 Bad Examples

```text
I am very passionate about AI and want to make the world better through technology.
```

```text
This project changes everything and will revolutionize sustainability forever.
```

```text
I used advanced AI to solve accessibility.
```

---

# 8. Concrete Page Layout Blueprint

## Home Page

```text
Navbar
Hero
Featured Work Grid
Metrics / Proof
Releaf Deep Feature
Sign Language AI Deep Feature
Athena AI Labs Internship Feature
iGEM Leadership Feature
Astrobio-gen Feature
Leadership Timeline
Skills System
FAQ
Contact CTA
Footer
```

## Work Page

```text
Project filter tabs:
All · AI/ML · Full-stack · Sustainability · Accessibility · Bio/Science · Leadership

Project card grid
```

## Research Page

```text
Astrobio-gen
Sustainability AI Model
Sign Language Translation
Computational Biology / iGEM
Future research roadmap
```

## Leadership Page

```text
iGEM Tech Lead
Rematter Cofounder
Carbon Footprint Club Tech Lead
Math Team Leader
Science Seed Founder
```

## Resume Page

```text
Embedded resume PDF viewer
Structured resume content in HTML
Download button
Contact CTA
```

---

# 9. Accessibility Requirements

Mandatory:

- Semantic HTML.
- Proper heading order.
- Keyboard-navigable menu and accordion.
- Visible focus rings.
- Alt text for all images.
- ARIA labels for icon-only buttons.
- Color contrast passes WCAG AA.
- Reduced motion support.
- Responsive layout from 360 px to desktop.

Focus ring:

```css
:focus-visible {
  outline: 3px solid rgba(0, 113, 227, 0.75);
  outline-offset: 4px;
}
```

---

# 10. Concrete Design Rules for Claude Code

Claude Code must follow these rules:

1. Do not create a generic portfolio template.
2. Do not use random bright gradients everywhere.
3. Do not use low-quality clipart.
4. Do not make every section a glass card.
5. Do not over-animate text.
6. Do not use tiny text for important technical content.
7. Do not use more than two primary typefaces.
8. Do not hardcode all content into component files.
9. Do not ignore mobile layout.
10. Do not use animation that breaks readability.
11. Do not copy Apple or Hack the North assets, logos, or illustrations.
12. Build an original visual system inspired by their patterns.
13. Prioritize project credibility over decorative noise.
14. Make the site fast, legible, responsive, and technically clean.
15. Treat each major project like a product launch section.

---

# 11. Recommended Aesthetic Summary

The website should look like a premium AI research/product portfolio:

- Apple gives the structure, polish, spacing, and restraint.
- Hack the North gives the immersive storytelling, visual layering, stats, FAQ, and community energy.
- Shengbo's own brand gives the scientific AI identity.

Final aesthetic:

```text
Dark scientific hero
Clean Apple-style product panels
Animated technical diagrams
Large stats blocks
Deep project case studies
Precise writing
Fast responsive implementation
```

---

# 12. Developer Build Checklist

Before considering the website complete, verify:

- Homepage has a strong hero and clear identity.
- Releaf, Sign Language AI, Athena AI Labs, iGEM, and Astrobio-gen each have detailed sections.
- Site has Apple-level spacing and typography discipline.
- Site has Hack-the-North-level narrative richness without copying its art.
- Animations are smooth and restrained.
- Mobile navigation works.
- FAQ accordion works.
- Project cards are data-driven.
- All external links open properly.
- Resume download works.
- Lighthouse performance is strong.
- Accessibility checks pass.
- The design feels premium, not template-generated.

---

# 13. Final Instruction for Claude Code

Build the portfolio as a polished, production-grade website using Next.js, TypeScript, Tailwind CSS, and Framer Motion. Use Apple as the reference for premium layout discipline and Hack the North as the reference for immersive section storytelling. Do not copy either website. Create an original scientific-AI visual identity centered on Shengbo Jiang's work in sustainability AI, sign-language translation, astrobiology AI, iGEM computational biology, and full-stack product engineering.

The final output should make a recruiter, professor, hackathon judge, or collaborator immediately understand that Shengbo is not simply listing activities. He is building serious AI systems with product direction, technical depth, and leadership execution.
