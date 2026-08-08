"""Renderer payloads for one immutable work variant source."""

from infrastructure.services.variant_document_content_payloads import (
    build_variant_document_content_payload,
)


class DjangoVariantDocumentPayloadBuilder:
    def __init__(self, task_payload_formatter=None):
        self.task_payload_formatter = task_payload_formatter

    def build(self, variant, request=None):
        variant_tasks = list(variant.tasks)
        content_payload = build_variant_document_content_payload(
            variant_id=variant.pk,
            variant_tasks=variant_tasks,
            content_blocks=variant.content_blocks,
            options=request.section.options if request else {},
            task_payload_formatter=self.task_payload_formatter,
            request=request,
        )
        return {
            'id': str(variant.pk),
            'number': variant.number,
            'title': f'Вариант {variant.number}',
            'max_score': variant.max_score_snapshot,
            'duration': variant.duration_snapshot,
            **content_payload,
        }
