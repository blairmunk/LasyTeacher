"""Resolve static assets for standalone HTML documents."""

from pathlib import Path

from django.contrib.staticfiles import finders


MATHJAX_SCRIPT = 'vendor/mathjax/es5/tex-chtml.js'


def document_asset_uri(asset_path: str) -> str:
    resolved_path = finders.find(asset_path)
    if not resolved_path:
        raise FileNotFoundError(
            f'Document static asset not found: {asset_path}'
        )
    return Path(resolved_path).resolve().as_uri()


def document_asset_context() -> dict[str, str]:
    return {
        'mathjax_script_url': document_asset_uri(MATHJAX_SCRIPT),
    }
