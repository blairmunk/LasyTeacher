"""Django-backed document payload builders for remedial sheets."""

from infrastructure.services.django_variant_document_payloads import (
    build_original_task_payload,
    build_variant_task_payload,
)
from infrastructure.services.document_build_cache import (
    document_payload_cache,
    document_section_input_key,
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


class DjangoRemedialHeaderPayloadBuilder:
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


class DjangoRemedialOriginalMistakesPayloadBuilder:
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


class DjangoRemedialTrainingTasksPayloadBuilder:
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
        payload = {
            **dict(request.section.options),
            'tasks': [
                build_variant_task_payload(
                    variant_task,
                    task_payload_formatter=self.task_payload_formatter,
                    request=request,
                )
                for variant_task in sheet_data.new_tasks or []
            ],
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
