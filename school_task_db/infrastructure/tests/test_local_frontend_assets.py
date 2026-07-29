from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import SimpleTestCase


VENDORED_ASSETS = (
    'vendor/bootstrap/css/bootstrap.min.css',
    'vendor/bootstrap/js/bootstrap.bundle.min.js',
    'vendor/fontawesome/css/all.min.css',
    'vendor/mathjax/es5/tex-chtml.js',
    'vendor/plotly/plotly-2.27.0.min.js',
)

EXTERNAL_ASSET_HOSTS = (
    'cdn.jsdelivr.net',
    'cdnjs.cloudflare.com',
    'cdn.plot.ly',
    'polyfill.io',
)


class LocalFrontendAssetTests(SimpleTestCase):
    def test_all_runtime_vendor_assets_are_available_locally(self):
        for asset_path in VENDORED_ASSETS:
            with self.subTest(asset_path=asset_path):
                self.assertIsNotNone(finders.find(asset_path))

    def test_base_template_uses_local_runtime_assets(self):
        html = render_to_string('base.html')

        self.assertIn('/static/vendor/bootstrap/css/bootstrap.min.css', html)
        self.assertIn('/static/vendor/bootstrap/js/bootstrap.bundle.min.js', html)
        self.assertIn('/static/vendor/fontawesome/css/all.min.css', html)
        self.assertIn('/static/vendor/mathjax/es5/tex-chtml.js', html)
        for host in EXTERNAL_ASSET_HOSTS:
            self.assertNotIn(host, html)

    def test_templates_do_not_reference_runtime_cdns(self):
        templates_dir = Path(settings.BASE_DIR) / 'templates'

        for template_path in templates_dir.rglob('*'):
            if not template_path.is_file():
                continue
            content = template_path.read_text(encoding='utf-8')
            for host in EXTERNAL_ASSET_HOSTS:
                with self.subTest(template=template_path.name, host=host):
                    self.assertNotIn(host, content)
