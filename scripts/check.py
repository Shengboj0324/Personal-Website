#!/usr/bin/env python3
"""Check static routes, fragment targets, metadata, and local asset references."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from asset_pipeline import browser_bundles

ROOT = Path(__file__).resolve().parent.parent

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.refs = []
        self.ids = set()
        self.headings = 0
        self.title = False
        self.description = False
        self.errors = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1': self.headings += 1
        if tag == 'title': self.title = True
        if tag == 'meta' and a.get('name') == 'description': self.description = bool(a.get('content'))
        if 'id' in a:
            if a['id'] in self.ids: self.errors.append(f'Duplicate ID: {a["id"]}')
            self.ids.add(a['id'])
        for attr in ('href', 'src'):
            if attr in a:
                self.refs.append(a[attr])
                if not a[attr] or a[attr] == '#': self.errors.append('Empty destination')
        if tag == 'img' and 'alt' not in a: self.errors.append('Image missing alt attribute')
        if tag == 'a' and a.get('target') == '_blank' and 'noopener' not in a.get('rel', '').split():
            self.errors.append('External tab link missing noopener')


def main():
    paths = [ROOT/'index.html', ROOT/'404.html', ROOT/'about/index.html', ROOT/'contact/index.html', *sorted((ROOT/'work').rglob('*.html'))]
    pages = {}
    errors = []
    for path in paths:
        page = Page(path)
        page.feed(path.read_text())
        pages[path] = page
        if page.headings != 1: page.errors.append(f'Expected 1 h1, found {page.headings}')
        if not page.title or not page.description: page.errors.append('Missing page metadata')
        errors.extend(f'{path.relative_to(ROOT)}: {e}' for e in page.errors)
    bundles = browser_bundles(ROOT)
    for name, expected in bundles.items():
        bundle = ROOT / name
        if not bundle.is_file() or bundle.read_bytes() != expected:
            errors.append(f'{name}: missing or stale browser bundle; rerun scripts/build.py')
    for path, page in pages.items():
        for name in bundles:
            if '/' + name not in page.refs:
                errors.append(f'{path.relative_to(ROOT)}: does not reference current bundle {name}')
        for ref in page.refs:
            if urlsplit(ref).path in ('/styles.css', '/app.js'):
                errors.append(f'{path.relative_to(ROOT)}: unversioned deployment asset {ref}')
    references = 0
    for path, page in pages.items():
        for ref in page.refs:
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc: continue
            references += 1
            target = ROOT/unquote(parsed.path).lstrip('/') if parsed.path.startswith('/') else path.parent/unquote(parsed.path)
            if not parsed.path: target = path
            elif target.is_dir(): target = target/'index.html'
            target = target.resolve()
            if not target.exists(): errors.append(f'{path.relative_to(ROOT)}: missing {ref}')
            elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f'{path.relative_to(ROOT)}: missing fragment {ref}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(pages)} pages; {references} local references; metadata, headings, links, and alt attributes.')

if __name__ == '__main__': main()
