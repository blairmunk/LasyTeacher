from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings

from core.context_processors import frontend_assets
from infrastructure.services.document_asset_urls import document_asset_context
from infrastructure.services.frontend_asset_urls import frontend_asset_urls


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
        html = render_to_string(
            'base.html',
            {'frontend_assets': frontend_asset_urls('local')},
        )

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

    @override_settings(FRONTEND_ASSET_MODE='cdn')
    def test_context_processor_selects_pinned_cdn_assets(self):
        assets = frontend_assets(None)['frontend_assets']

        self.assertEqual(
            assets['bootstrap_css'],
            'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/'
            'dist/css/bootstrap.min.css',
        )
        self.assertEqual(
            assets['mathjax_js'],
            'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js',
        )
        self.assertEqual(
            assets['plotly_js'],
            'https://cdn.plot.ly/plotly-2.27.0.min.js',
        )

    @override_settings(FRONTEND_ASSET_MODE='cdn')
    def test_standalone_documents_keep_local_mathjax_in_cdn_mode(self):
        self.assertTrue(
            document_asset_context()['mathjax_script_url'].startswith(
                'file://'
            )
        )

    def test_rejects_unknown_frontend_asset_mode(self):
        with self.assertRaises(ImproperlyConfigured):
            frontend_asset_urls('automatic')
