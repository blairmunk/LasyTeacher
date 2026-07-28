"""Django-backed document payload builders for regular works."""

from core_logic.value_objects.document_recipes import (
    TASK_LIST_SECTION,
)
from infrastructure.services.django_variant_document_payloads import (
    DjangoVariantDocumentPayloadBuilder,
)
from works.models import Work


class DjangoWorkHeaderPayloadBuilder:
    def __init__(self, get_work_source=None):
        self.get_work_source = get_work_source or _get_work_source

    def build_payload(self, request):
        work = self.get_work_source(request.source.source_id)
        variant = _work_variant_from_request(work, request)
        title = work.name
        duration = work.duration
        max_score = work.effective_max_score
        if variant is not None:
            title = f'{work.name}. Вариант {variant.number}'
            duration = variant.display_duration
            max_score = variant.display_max_score
        return {
            **dict(request.section.options),
            'title': title,
            'work_type': work.work_type,
            'duration': duration,
            'max_score': max_score,
        }


class DjangoWorkTaskListPayloadBuilder:
    def __init__(
        self,
        get_work_source=None,
        task_payload_formatter=None,
        variant_payload_builder=None,
    ):
        self.get_work_source = get_work_source or _get_work_source
        self.variant_payload_builder = (
            variant_payload_builder
            or DjangoVariantDocumentPayloadBuilder(
                task_payload_formatter=task_payload_formatter,
            )
        )

    def build_payload(self, request):
        work = self.get_work_source(request.source.source_id)
        variants = [
            self.variant_payload_builder.build(
                variant,
                request=request,
            )
            for variant in _work_variants_from_request(work, request)
        ]
        return {
            **dict(request.section.options),
            'variants': variants,
        }


def _get_work_source(work_id):
    return Work.objects.get(pk=work_id)


def _work_variants_from_request(work, request):
    variants = work.variant_set.order_by('number', 'pk')
    variant_id = request.section.options.get('variant_id')
    if variant_id:
        variants = variants.filter(pk=variant_id)
    return variants


def _work_variant_from_request(work, request):
    variant_id = request.section.options.get('variant_id')
    if not variant_id:
        return None
    return work.variant_set.filter(pk=variant_id).first()
