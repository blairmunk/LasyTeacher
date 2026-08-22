# Vendored frontend assets

These files are committed so the application and document rendering work
without internet access.

- Bootstrap 5.1.3
- Font Awesome Free 6.0.0
- MathJax 3.2.2
- Plotly.js 2.27.0

Each package directory contains its upstream license.

The files were taken from the corresponding npm release archives. Runtime
templates must reference these copies through Django static files or, for
standalone documents, through the document asset resolver.

Browser UI assets are local by default. An online deployment can use the
pinned CDN copies instead:

```bash
FRONTEND_ASSET_MODE=cdn ../venv/bin/python manage.py runserver
```

Allowed values are `local` and `cdn`. Standalone HTML documents and PDF
rendering deliberately stay local in both modes.
