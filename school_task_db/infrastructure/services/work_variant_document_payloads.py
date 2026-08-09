"""Renderer payloads for one immutable work variant source."""

from core_logic.value_objects.document_recipes import TASK_LIST_SECTION
from infrastructure.services.variant_document_content_payloads import (
    build_variant_ordered_content_payload,
    build_variant_task_collection_payload,
)


class WorkVariantDocumentPayloadBuilder:
    def __init__(self, task_payload_formatter=None):
        self.task_payload_formatter = task_payload_formatter

    def build(self, variant, request=None):
        variant_tasks = list(variant.tasks)
        if request and request.section.section_type == TASK_LIST_SECTION:
            content_payload = build_variant_ordered_content_payload(
                variant_id=variant.pk,
                variant_tasks=variant_tasks,
                content_blocks=variant.content_blocks,
                options=request.section.options,
                task_payload_formatter=self.task_payload_formatter,
                request=request,
            )
        else:
            content_payload = build_variant_task_collection_payload(
                variant_tasks=variant_tasks,
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
