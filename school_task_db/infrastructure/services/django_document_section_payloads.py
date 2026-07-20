"""Django-backed payload builders for document sections."""

from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TASK_VARIANTS_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.entities.document import (
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from works.models import Work


class DjangoWorkHeaderPayloadBuilder:
    def __init__(self, get_work_source=None):
        self.get_work_source = get_work_source or _get_work_source

    def build_payload(self, request):
        work = self.get_work_source(request.source.source_id)
        return {
            **dict(request.section.options),
            'title': work.name,
            'work_type': work.work_type,
            'duration': work.duration,
            'max_score': work.effective_max_score,
        }


class DjangoWorkTaskVariantsPayloadBuilder:
    def __init__(self, get_work_source=None, task_payload_formatter=None):
        self.get_work_source = get_work_source or _get_work_source
        self.task_payload_formatter = task_payload_formatter

    def build_payload(self, request):
        work = self.get_work_source(request.source.source_id)
        variants = [
            _work_variant_payload(
                variant,
                task_payload_formatter=self.task_payload_formatter,
                request=request,
            )
            for variant in work.variant_set.order_by('number', 'pk')
        ]
        return {
            **dict(request.section.options),
            'variants': variants,
        }


class RemedialSheetDataProvider:
    def __init__(self, get_remedial_sheet_data=None):
        self.get_remedial_sheet_data = (
            get_remedial_sheet_data
            or GetRemedialSheetDataUseCase(
                work_repo=DjangoWorkRepository(),
            ).execute
        )
        self._cache = {}

    def get(self, variant_id):
        if variant_id not in self._cache:
            self._cache[variant_id] = self.get_remedial_sheet_data(variant_id)
        return self._cache[variant_id]


class DjangoRemedialHeaderPayloadBuilder:
    def __init__(self, sheet_data_provider):
        self.sheet_data_provider = sheet_data_provider

    def build_payload(self, request):
        sheet_data = self.sheet_data_provider.get(request.source.source_id)
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
        sheet_data = self.sheet_data_provider.get(request.source.source_id)
        return {
            **dict(request.section.options),
            'tasks': [
                _original_task_payload(
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
        sheet_data = self.sheet_data_provider.get(request.source.source_id)
        return {
            **dict(request.section.options),
            'tasks': [
                _variant_task_payload(
                    variant_task,
                    task_payload_formatter=self.task_payload_formatter,
                    request=request,
                )
                for variant_task in sheet_data.new_tasks or []
            ],
        }


def build_work_section_payload_builder_registry(
    get_work_source=None,
    task_payload_formatter=None,
) -> DocumentSectionPayloadBuilderRegistry:
    registry = DocumentSectionPayloadBuilderRegistry()
    registry.register(
        HEADER_SECTION,
        DjangoWorkHeaderPayloadBuilder(get_work_source=get_work_source),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        TASK_VARIANTS_SECTION,
        DjangoWorkTaskVariantsPayloadBuilder(
            get_work_source=get_work_source,
            task_payload_formatter=task_payload_formatter,
        ),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        TASK_LIST_SECTION,
        DjangoWorkTaskVariantsPayloadBuilder(
            get_work_source=get_work_source,
            task_payload_formatter=task_payload_formatter,
        ),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    for section_type in (
        ANSWERS_SECTION,
        ANSWER_KEY_SECTION,
        SHORT_SOLUTIONS_SECTION,
        FULL_SOLUTIONS_SECTION,
    ):
        registry.register(
            section_type,
            DjangoWorkTaskVariantsPayloadBuilder(
                get_work_source=get_work_source,
                task_payload_formatter=task_payload_formatter,
            ),
            document_type=WORK_DOCUMENT_TYPE,
            source_type=WORK_SOURCE_TYPE,
        )
    return registry


def build_remedial_sheet_section_payload_builder_registry(
    get_remedial_sheet_data=None,
    task_payload_formatter=None,
) -> DocumentSectionPayloadBuilderRegistry:
    sheet_data_provider = RemedialSheetDataProvider(
        get_remedial_sheet_data=get_remedial_sheet_data,
    )
    registry = DocumentSectionPayloadBuilderRegistry()
    registry.register(
        HEADER_SECTION,
        DjangoRemedialHeaderPayloadBuilder(sheet_data_provider),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
    )
    registry.register(
        ORIGINAL_MISTAKES_SECTION,
        DjangoRemedialOriginalMistakesPayloadBuilder(
            sheet_data_provider,
            task_payload_formatter=task_payload_formatter,
        ),
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
    )
    for section_type in (
        TRAINING_TASKS_SECTION,
        ANSWERS_SECTION,
        SHORT_SOLUTIONS_SECTION,
        FULL_SOLUTIONS_SECTION,
    ):
        registry.register(
            section_type,
            DjangoRemedialTrainingTasksPayloadBuilder(
                sheet_data_provider,
                task_payload_formatter=task_payload_formatter,
            ),
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
        )
    return registry


def _get_work_source(work_id):
    return Work.objects.get(pk=work_id)


def _work_variant_payload(variant, task_payload_formatter=None, request=None):
    variant_tasks = (
        variant.varianttask_set
        .select_related(
            'task',
            'task__topic',
            'task__subtopic',
            'task__source',
        )
        .order_by('order', 'pk')
    )
    return {
        'id': str(variant.pk),
        'number': variant.number,
        'title': f'Вариант {variant.number}',
        'max_score': variant.display_max_score,
        'duration': variant.display_duration,
        'tasks': [
            _variant_task_payload(
                variant_task,
                task_payload_formatter=task_payload_formatter,
                request=request,
            )
            for variant_task in variant_tasks
        ],
    }


def _variant_task_payload(
    variant_task,
    task_payload_formatter=None,
    request=None,
):
    task = variant_task.task
    payload = {
        **_task_payload(task),
        'order': variant_task.order,
        'max_points': variant_task.max_points,
    }
    return _format_task_payload(payload, task_payload_formatter, request=request)


def _original_task_payload(task_row, task_payload_formatter=None, request=None):
    payload = {
        **_task_payload(task_row.task),
        'order': task_row.order,
        'points': task_row.points,
        'max_points': task_row.max_points,
        'pct': task_row.pct,
        'status': task_row.status,
        'group_name': task_row.group_name,
    }
    return _format_task_payload(payload, task_payload_formatter, request=request)


def _task_payload(task):
    return {
        'id': str(task.pk),
        'text': task.text,
        'answer': task.answer,
        'short_solution': task.short_solution,
        'full_solution': task.full_solution,
        'hint': task.hint,
        'instruction': task.instruction,
        'task_type': task.task_type,
        'difficulty': task.difficulty,
        'topic': task.topic.name if task.topic else '',
        'subtopic': task.subtopic.name if task.subtopic else '',
        'source': str(task.source) if task.source else '',
        'source_detail': task.source_detail,
    }


def _format_task_payload(payload, task_payload_formatter=None, request=None):
    if task_payload_formatter is None:
        return payload
    return task_payload_formatter.format_task_payload(payload, request=request)


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
