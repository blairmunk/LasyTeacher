"""Select browser UI assets for offline or CDN-backed deployments."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static


FRONTEND_ASSET_MODE_LOCAL = 'local'
FRONTEND_ASSET_MODE_CDN = 'cdn'
FRONTEND_ASSET_MODES = {
    FRONTEND_ASSET_MODE_LOCAL,
    FRONTEND_ASSET_MODE_CDN,
}

LOCAL_FRONTEND_ASSETS = {
    'bootstrap_css': 'vendor/bootstrap/css/bootstrap.min.css',
    'bootstrap_js': 'vendor/bootstrap/js/bootstrap.bundle.min.js',
    'fontawesome_css': 'vendor/fontawesome/css/all.min.css',
    'mathjax_js': 'vendor/mathjax/es5/tex-chtml.js',
    'plotly_js': 'vendor/plotly/plotly-2.27.0.min.js',
}

CDN_FRONTEND_ASSETS = {
    'bootstrap_css': (
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/'
        'dist/css/bootstrap.min.css'
    ),
    'bootstrap_js': (
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/'
        'dist/js/bootstrap.bundle.min.js'
    ),
    'fontawesome_css': (
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/'
        'css/all.min.css'
    ),
    'mathjax_js': (
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js'
    ),
    'plotly_js': 'https://cdn.plot.ly/plotly-2.27.0.min.js',
}


def frontend_asset_urls(mode: str | None = None) -> dict[str, str]:
    selected_mode = (
        mode
        if mode is not None
        else getattr(settings, 'FRONTEND_ASSET_MODE', FRONTEND_ASSET_MODE_LOCAL)
    )
    selected_mode = str(selected_mode).strip().lower()
    if selected_mode not in FRONTEND_ASSET_MODES:
        raise ImproperlyConfigured(
            'FRONTEND_ASSET_MODE must be "local" or "cdn"'
        )
    if selected_mode == FRONTEND_ASSET_MODE_CDN:
        return dict(CDN_FRONTEND_ASSETS)
    return {
        name: static(asset_path)
        for name, asset_path in LOCAL_FRONTEND_ASSETS.items()
    }
