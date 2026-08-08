"""Django-backed document payload builders for regular works."""

from core_logic.value_objects.document_recipes import (
    TASK_LIST_SECTION,
)
from core_logic.services.work_score_allocation_service import (
    WorkScoreAllocationService,
    WorkScoreSpecRow,
)
from infrastructure.services.document_build_cache import (
    document_payload_cache,
    document_section_input_key,
)
from infrastructure.repositories.django_work_document_repo import (
    DjangoWorkDocumentRepository,
)
from infrastructure.services.work_variant_document_payloads import (
    WorkVariantDocumentPayloadBuilder,
)


class WorkDocumentSourceProvider:
    def __init__(
        self,
        work_document_repo=None,
        get_work_document_source=None,
    ):
        self.get_work_document_source = (
            get_work_document_source
            or (
                work_document_repo or DjangoWorkDocumentRepository()
            ).get_work_document_source
        )

    def get(self, work_id, build_context=None):
        if build_context is None:
            return self.get_work_document_source(work_id)
        cache = build_context.setdefault('work_document_source_by_id', {})
        if work_id not in cache:
            cache[work_id] = self.get_work_document_source(work_id)
        return cache[work_id]


class DjangoWorkHeaderPayloadBuilder:
    def __init__(
        self,
        get_work_document_source=None,
        work_source_provider=None,
        score_allocation_service=None,
    ):
        self.work_source_provider = (
            work_source_provider
            or WorkDocumentSourceProvider(
                get_work_document_source=get_work_document_source,
            )
        )
        self.score_allocation_service = (
            score_allocation_service or WorkScoreAllocationService()
        )

    def build_payload(self, request):
        work = self.work_source_provider.get(
            request.source.source_id,
            request.build_context,
        )
        variant = _work_variant_from_request(work, request)
        title = work.name
        duration = work.duration
        if variant is None:
            score_spec_rows = (
                WorkScoreSpecRow(
                    spec_row_id=row.pk,
                    count=row.count,
                    weight=row.weight,
                    is_assessable=row.is_assessable,
                )
                for row in work.score_spec_rows
            )
            max_score = self.score_allocation_service.effective_max_score(
                max_score=work.max_score,
                spec_rows=score_spec_rows,
            )
        else:
            title = f'{work.name}. Вариант {variant.number}'
            duration = variant.duration_snapshot
            max_score = variant.max_score_snapshot
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
        get_work_document_source=None,
        task_payload_formatter=None,
        variant_payload_builder=None,
        work_source_provider=None,
    ):
        self.work_source_provider = (
            work_source_provider
            or WorkDocumentSourceProvider(
                get_work_document_source=get_work_document_source,
            )
        )
        self.variant_payload_builder = (
            variant_payload_builder
            or WorkVariantDocumentPayloadBuilder(
                task_payload_formatter=task_payload_formatter,
            )
        )

    def build_payload(self, request):
        cache = document_payload_cache(
            request,
            namespace='work_variant_payloads',
        )
        cache_key = document_section_input_key(request)
        if cache_key in cache:
            return cache[cache_key]

        work = self.work_source_provider.get(
            request.source.source_id,
            request.build_context,
        )
        variants = [
            self.variant_payload_builder.build(
                variant,
                request=request,
            )
            for variant in _work_variants_from_request(work, request)
        ]
        payload = {
            **dict(request.section.options),
            'variants': variants,
        }
        cache[cache_key] = payload
        return payload


def _work_variants_from_request(work, request):
    variants = work.variants
    variant_id = request.section.options.get('variant_id')
    if variant_id:
        variants = tuple(
            variant for variant in variants
            if variant.pk == str(variant_id)
        )
    return variants


def _work_variant_from_request(work, request):
    variant_id = request.section.options.get('variant_id')
    if not variant_id:
        return None
    return next(
        (
            variant for variant in work.variants
            if variant.pk == str(variant_id)
        ),
        None,
    )
