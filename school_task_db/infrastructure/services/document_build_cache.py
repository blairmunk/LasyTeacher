"""Build-scoped cache helpers for document section payloads."""

import json


def document_payload_cache(request, namespace):
    caches = request.build_context.setdefault('document_payload_cache', {})
    return caches.setdefault(namespace, {})


def document_section_input_key(request):
    render_target = request.render_target
    return (
        request.source.source_type,
        request.source.source_id,
        request.section.section_type,
        render_target.renderer_type if render_target else '',
        render_target.page_format if render_target else '',
        json.dumps(
            dict(request.section.options),
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ),
    )
