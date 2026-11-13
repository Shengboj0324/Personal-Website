"""Create content-addressed browser bundles so deployments cannot reuse stale code."""
from hashlib import sha256
from pathlib import Path


def browser_bundles(root: Path) -> dict[str, bytes]:
    stylesheet = (root / 'styles.css').read_text(encoding='utf-8')
    font_import = "@import url('/assets/fonts.css');"
    if stylesheet.count(font_import) != 1:
        raise ValueError('Expected exactly one local font import in styles.css')
    fonts = (root / 'assets/fonts.css').read_text(encoding='utf-8')
    fonts += (root / 'assets/arabic-fonts.css').read_text(encoding='utf-8')
    fonts += (root / 'assets/devanagari-fonts.css').read_text(encoding='utf-8')
    css = stylesheet.replace(font_import, fonts, 1).encode('utf-8')
    javascript = (root / 'app.js').read_bytes()
    # world.js is the bundled 3D layer (three.js plus src/world), built with `npm run world`.
    world = (root / 'world.js').read_bytes()
    bundles = {
        f'assets/portfolio.{sha256(data).hexdigest()[:16]}.{extension}': data
        for extension, data in [('css', css), ('js', javascript)]
    }
    bundles[f'assets/world.{sha256(world).hexdigest()[:16]}.js'] = world
    return bundles


def is_optional(name: str) -> bool:
    """The 3D bundle is only referenced by pages that have a 3D scene."""
    return '/world.' in name
