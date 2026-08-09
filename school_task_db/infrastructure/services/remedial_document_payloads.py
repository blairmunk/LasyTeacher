"""Document payload builders for remedial sheets."""

from core_logic.value_objects.document_recipes import TRAINING_TASKS_SECTION
from infrastructure.services.document_build_cache import (
    document_payload_cache,
    document_section_input_key,
)
from infrastructure.services.task_document_payloads import (
    build_original_task_payload,
)
from infrastructure.services.variant_document_content_payloads import (
    build_variant_ordered_content_payload,
    build_variant_task_collection_payload,
)


class RemedialSheetDataProvider:
    def __init__(self, get_remedial_sheet_data=None):
        if get_remedial_sheet_data is None:
            raise ValueError('get_remedial_sheet_data is required')
        self.get_remedial_sheet_data = get_remedial_sheet_data

    def get(self, variant_id, build_context=None):
        if build_context is None:
            return self.get_remedial_sheet_data(variant_id)
        cache = build_context.setdefault('remedial_sheet_data_by_variant', {})
        if variant_id not in cache:
            cache[variant_id] = self.get_remedial_sheet_data(variant_id)
        return cache[variant_id]


class RemedialHeaderPayloadBuilder:
    def __init__(self, sheet_data_provider):
        self.sheet_data_provider = sheet_data_provider

    def build_payload(self, request):
        sheet_data = self.sheet_data_provider.get(
            _remedial_variant_id(request),
            request.build_context,
        )
        return {
            **dict(request.section.options),
            'title': 'Работа над ошибками',
            'student': _student_payload(sheet_data.student),
            'source_work': _work_ref_payload(sheet_data.source_work),
            'mark': _mark_payload(sheet_data.mark),
        }


class RemedialOriginalMistakesPayloadBuilder:
    def __init__(self, sheet_data_provider, task_payload_formatter=None):
        self.sheet_data_provider = sheet_data_provider
        self.task_payload_formatter = task_payload_formatter

    def build_payload(self, request):
        sheet_data = self.sheet_data_provider.get(
            _remedial_variant_id(request),
            request.build_context,
        )
        return {
            **dict(request.section.options),
            'tasks': [
                build_original_task_payload(
                    task_row,
                    task_payload_formatter=self.task_payload_formatter,
                    request=request,
                )
                for task_row in sheet_data.original_tasks
            ],
        }


class RemedialVariantSectionPayloadBuilder:
    def __init__(self, sheet_data_provider, task_payload_formatter=None):
        self.sheet_data_provider = sheet_data_provider
        self.task_payload_formatter = task_payload_formatter

    def build_payload(self, request):
        cache = document_payload_cache(
            request,
            namespace='remedial_training_task_payloads',
        )
        cache_key = document_section_input_key(request)
        if cache_key in cache:
            return cache[cache_key]

        sheet_data = self.sheet_data_provider.get(
            _remedial_variant_id(request),
            request.build_context,
        )
        if request.section.section_type == TRAINING_TASKS_SECTION:
            content_payload = build_variant_ordered_content_payload(
                variant_id=_remedial_variant_id(request),
                variant_tasks=sheet_data.new_tasks or (),
                content_blocks=sheet_data.content_blocks or (),
                options=request.section.options,
                task_payload_formatter=self.task_payload_formatter,
                request=request,
            )
        else:
            content_payload = build_variant_task_collection_payload(
                variant_tasks=sheet_data.new_tasks or (),
                task_payload_formatter=self.task_payload_formatter,
                request=request,
            )
        payload = {
            **dict(request.section.options),
            **content_payload,
        }
        cache[cache_key] = payload
        return payload


def _remedial_variant_id(request):
    return request.section.options.get('variant_id') or request.source.source_id


def _student_payload(student):
    if not student:
        return None
    return {
        'id': student.pk,
        'full_name': student.full_name,
        'short_name': student.short_name,
    }


def _work_ref_payload(work):
    if not work:
        return None
    return {
        'id': str(work.pk),
        'name': work.name,
    }


def _mark_payload(mark):
    if not mark:
        return None
    return {
        'score': mark.score,
        'points': mark.points,
        'max_points': mark.max_points,
    }
