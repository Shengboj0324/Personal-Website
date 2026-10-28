"""Focused regression tests for static localization boundaries."""
import unittest
from i18n import Localizer, selector


class LocalizationTests(unittest.TestCase):
    def render(self, html, catalog=None, language='fr'):
        parser = Localizer(language, catalog, ['/', '/work/', '/work/releaf/'])
        parser.feed(html)
        return ''.join(parser.parts)

    def test_same_page_and_assets_keep_their_destinations(self):
        html = '<a href="/work/?category=Research#list">Work</a><a href="https://example.com/work/">Source</a><img src="/assets/example.png" alt=""><button data-url="/work/releaf/">1</button><a href="#main">Go</a>'
        result = self.render(html, {'Work': 'Projets', 'Source': 'Source', 'Go': 'Aller'})
        self.assertIn('href="/fr/work/?category=Research#list"', result)
        self.assertIn('data-url="/fr/work/releaf/"', result)
        self.assertIn('href="https://example.com/work/"', result)
        self.assertIn('src="/assets/example.png"', result)
        self.assertIn('href="#main"', result)

    def test_filter_ids_remain_stable_while_display_labels_change(self):
        html = '<article data-category="Research"><p>Research</p></article><button data-filter="Research">Research</button><button data-record-index="0" data-category="Research">01</button>'
        result = self.render(html, {'Research': 'Recherche'})
        self.assertIn('<article data-category="Research"><p>Recherche</p>', result)
        self.assertIn('data-filter="Research">Recherche</button>', result)
        self.assertIn('data-record-index="0" data-category="Recherche"', result)

    def test_translation_is_escaped_and_executable_text_is_untouched(self):
        result = self.render('<p>Hello</p><img alt="Hello"><script>const word = "Hello";</script>', {'Hello': '<bonjour> & "salut"'})
        self.assertIn('&lt;bonjour&gt; &amp; "salut"</p>', result)
        self.assertIn('alt="&lt;bonjour&gt; &amp; &quot;salut&quot;"', result)
        self.assertIn('<script>const word = "Hello";</script>', result)

    def test_missing_copy_fails_instead_of_silently_leaving_english(self):
        with self.assertRaisesRegex(ValueError, 'missing translation'):
            self.render('<p>Untranslated sentence.</p>', {})

    def test_arabic_document_and_selector(self):
        result = self.render('<html lang="en"><p>Hello</p></html>', {'Hello': 'مرحبًا'}, 'ar')
        self.assertIn('lang="ar" dir="rtl" data-locale-prefix="/ar"', result)
        picker = selector('/work/releaf/', 'ar', lambda value: value)
        self.assertIn('href="/ar/work/releaf/" lang="ar" dir="auto" hreflang="ar" aria-current="true"', picker)
        self.assertIn('href="/zh-hant/work/releaf/"', picker)
        self.assertIn('href="/work/releaf/" lang="en"', picker)


if __name__ == '__main__':
    unittest.main()
