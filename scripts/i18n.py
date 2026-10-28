"""Build static language editions from checked-in, complete translation catalogs.

Catalogs contain public editorial text only. Building or visiting the site never
contacts a translation service. URLs, code, filters, and product names stay stable.
"""
import json
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = 'https://www.shengbojiang.me'
LANGUAGES = {
    'en': ('English', ''),
    'zh-Hans': ('简体中文', 'zh-hans'),
    'zh-Hant': ('繁體中文', 'zh-hant'),
    'ja': ('日本語', 'ja'),
    'es': ('Español', 'es'),
    'fr': ('Français', 'fr'),
    'de': ('Deutsch', 'de'),
    'ar': ('العربية', 'ar'),
}
MESSAGES = {
    'menuOpen': 'Open navigation menu',
    'menuClose': 'Close navigation menu',
    'countOne': '{count} project',
    'countTwo': 'Two projects',
    'countMany': '{count} projects',
    'copied': 'Email address copied.',
    'copyFailed': 'Copy unavailable. Select the email address above, or click it to write.',
    'pause': 'Pause motion',
    'resume': 'Resume motion',
    'reduced': 'Reduced motion',
    'position': '{index} of {total}: {title}',
    'openCase': 'Open {title} case study',
}
EXTRA_TEXT = {
    'Choose language', 'Language', 'Original project media is shown in its source language.',
    'Résumé (English)', 'Download résumé (English)', *MESSAGES.values(),
}
# Identity, programming terminology, and named products should not be translated.
KEEP = {
    'Shengbo Jiang', 'Shengbo.', 'sj.', 'Releaf', 'releaf.', 'CollegeAdvisor',
    'ZenithSync Assay Planner', 'Pioneer Academics', 'Athena AI Labs',
    'Rematter Cooperation', 'Science Seed Project', 'Kehillah Sailbot',
    'Hamden Hall', 'LCG-China · iGEM', 'GitHub', 'Hugging Face', 'Kaggle', 'LinkedIn',
    'Python, Swift, Java, JavaScript, TypeScript, SQL',
    'SwiftUI, Django, FastAPI, React / Next.js, PostgreSQL, Git, Docker',
}
TRANSLATED_ATTRIBUTES = {'alt', 'aria-label', 'aria-valuetext', 'data-title', 'data-summary'}


def translatable(value):
    return bool(re.search(r'[A-Za-z]', value)) and value not in KEEP and '@' not in value


def route_for(path, language):
    prefix = LANGUAGES[language][1]
    return f'/{prefix}{path}' if prefix else path


def file_for(route):
    return route.lstrip('/') + ('index.html' if route.endswith('/') else '')


class Localizer(HTMLParser):
    def __init__(self, language='en', catalog=None, routes=()):
        super().__init__(convert_charrefs=True)
        self.language = language
        self.catalog = catalog
        self.routes = set(routes)
        self.parts = []
        self.strings = set()
        self.raw_tag = None

    def translate(self, value):
        stripped = value.strip()
        if not translatable(stripped):
            return value
        self.strings.add(stripped)
        if self.catalog is None:
            return value
        if stripped not in self.catalog:
            raise ValueError(f'{self.language}: missing translation: {stripped}')
        return value.replace(stripped, self.catalog[stripped], 1)

    def link(self, value):
        url = urlsplit(value)
        if not url.scheme and not url.netloc and url.path in self.routes:
            return urlunsplit(('', '', route_for(url.path, self.language), url.query, url.fragment))
        return value

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ('script', 'style'):
            self.raw_tag = tag
        result = []
        for key, value in attrs:
            if value is not None:
                if tag == 'html' and key == 'lang':
                    value = self.language
                elif key in ('href', 'data-url'):
                    value = self.link(value)
                elif key in TRANSLATED_ATTRIBUTES or (key == 'data-category' and tag == 'button'):
                    value = self.translate(value)
                elif tag == 'meta' and key == 'content' and (
                    values.get('name') == 'description' or values.get('property') in ('og:title', 'og:description')
                ):
                    value = self.translate(value)
            result.append(key if value is None else f'{key}="{escape(value, quote=True)}"')
        if tag == 'html':
            result.append(f'dir="{"rtl" if self.language == "ar" else "ltr"}"')
            result.append(f'data-locale-prefix="{route_for("/", self.language).rstrip("/")}"')
        self.parts.append('<' + tag + (' ' + ' '.join(result) if result else '') + '>')

    def handle_endtag(self, tag):
        self.parts.append(f'</{tag}>')
        if tag == self.raw_tag:
            self.raw_tag = None

    def handle_data(self, data):
        self.parts.append(data if self.raw_tag else escape(self.translate(data), quote=False))

    def handle_decl(self, decl):
        self.parts.append(f'<!{decl}>')

    def handle_comment(self, data):
        self.parts.append(f'<!--{data}-->')


def collect_strings(pages):
    strings = {s for s in EXTRA_TEXT if translatable(s)}
    for html in pages.values():
        parser = Localizer()
        parser.feed(html)
        strings.update(parser.strings)
    return sorted(strings)


def selector(route, language, translate):
    name = LANGUAGES[language][0]
    options = ''.join(
        f'<a href="{route_for(route, code)}" lang="{code}" dir="auto" '
        f'hreflang="{code}"{(" aria-current=\"true\"" if code == language else "")}>'
        f'{label}<span aria-hidden="true">{"✓" if code == language else ""}</span></a>'
        for code, (label, _) in LANGUAGES.items()
    )
    return (
        '<details class="language-picker">'
        f'<summary aria-label="{escape(translate("Choose language"), quote=True)}">'
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
        'stroke-width="1.4" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
        '<ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6h14M5 18h14"/></svg>'
        f'<span lang="{language}" dir="auto">{name}</span><span class="language-chevron" aria-hidden="true">⌄</span></summary>'
        f'<nav class="language-options" aria-label="{escape(translate("Language"), quote=True)}">{options}</nav></details>'
    )


def render_editions(pages):
    expected = set(collect_strings(pages))
    for language in LANGUAGES:
        catalog = None
        if language != 'en':
            catalog = json.loads((ROOT / 'content/locales' / f'{language}.json').read_text())
            missing = expected - catalog.keys()
            if missing:
                raise ValueError(f'{language}: {len(missing)} missing translations: {sorted(missing)[:3]}')
            for source in expected:
                translated = catalog[source]
                if not isinstance(translated, str) or not translated.strip():
                    raise ValueError(f'{language}: empty translation for {source}')
                if sorted(re.findall(r'\{\w+\}', source)) != sorted(re.findall(r'\{\w+\}', translated)):
                    raise ValueError(f'{language}: invalid placeholders for {source}')
        for route, html in pages.items():
            parser = Localizer(language, catalog, pages)
            parser.feed(html)
            result = ''.join(parser.parts)
            translate = lambda text: catalog[text] if catalog is not None and text in catalog else text
            picker = selector(route, language, translate)
            result = result.replace('</header>', picker + '</header>', 1)
            messages = json.dumps({key: translate(value) for key, value in MESSAGES.items()}, ensure_ascii=False).replace('<', '\\u003c')
            result = result.replace('</head>', f'<script id="locale-messages" type="application/json">{messages}</script></head>', 1)
            if route != '/404.html':
                seo = f'<link rel="canonical" href="{ORIGIN}{route_for(route, language)}">'
                seo += ''.join(f'<link rel="alternate" hreflang="{code}" href="{ORIGIN}{route_for(route, code)}">' for code in LANGUAGES)
                seo += f'<link rel="alternate" hreflang="x-default" href="{ORIGIN}{route}">'
            else:
                seo = '<meta name="robots" content="noindex">'
            result = result.replace('</head>', seo + '</head>', 1)
            if language != 'en':
                if route == '/':
                    rich = json.loads((ROOT / 'content/locales/rich-headings.json').read_text())
                    result = re.sub(r'(<section class="home-about shell">.*?<h2>).*?(</h2>)', lambda match: match[1] + rich[language] + match[2], result, count=1, flags=re.S)
                result = result.replace('>' + translate('Résumé') + ' <span', '>' + translate('Résumé (English)') + ' <span')
                result = result.replace('>' + translate('Download résumé') + ' <span', '>' + translate('Download résumé (English)') + ' <span')
                if '/work/' in route and route != '/work/':
                    result = result.replace('<section class="case-intro', '<p class="source-language-note shell">' + escape(translate('Original project media is shown in its source language.')) + '</p><section class="case-intro', 1)
            yield file_for(route_for(route, language)), result
