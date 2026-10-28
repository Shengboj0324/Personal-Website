#!/usr/bin/env python3
"""Verify deployed HTML uses the current bundles and the CDN serves their exact bytes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from asset_pipeline import browser_bundles
from check import Page, ROOT
from i18n import LANGUAGES


def fetch(base, path):
    request = Request(urljoin(base, path), headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get_content_type()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base_url', help='Deployed site origin, for example https://www.shengbojiang.me/')
    args = parser.parse_args()
    origin = urlsplit(args.base_url)
    if origin.scheme not in ('http', 'https') or not origin.netloc or origin.path not in ('', '/'):
        parser.error('base_url must be an HTTP(S) origin without a path')
    bundles = browser_bundles(ROOT)
    pages = [ROOT/'index.html', ROOT/'about/index.html', ROOT/'contact/index.html', *sorted((ROOT/'work').rglob('index.html'))]

    for _, prefix in LANGUAGES.values():
        if prefix: pages.extend(sorted((ROOT / prefix).rglob('index.html')))

    def check_page(path):
        route = '/' + path.relative_to(ROOT).as_posix().removesuffix('index.html')
        data, mime = fetch(args.base_url, route)
        if mime != 'text/html':
            raise ValueError(f'{route}: expected HTML, received {mime}')
        page = Page(path)
        page.feed(data.decode('utf-8'))
        local_page = Page(path)
        local_page.feed(path.read_text())
        if page.language != local_page.language or page.direction != local_page.direction:
            raise ValueError(f'{route}: deployed language or direction differs from build')
        if sorted(page.language_links) != sorted(LANGUAGES):
            raise ValueError(f'{route}: missing deployed language selector')
        for bundle in bundles:
            if '/' + bundle not in page.refs:
                raise ValueError(f'{route}: deployed HTML does not reference {bundle}')
        return route

    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = list(pool.map(check_page, pages))
    for name, expected in bundles.items():
        data, mime = fetch(args.base_url, '/' + name)
        allowed = ('text/css',) if name.endswith('.css') else ('text/javascript', 'application/javascript')
        if mime not in allowed or data != expected:
            raise ValueError(f'/{name}: deployed bundle differs from the build or has incorrect MIME type ({mime})')
    print(f'PASS: {len(checked)} live routes reference current bundles; deployed CSS and JavaScript match the build byte for byte.')


if __name__ == '__main__':
    main()
