"""Django-backed payload builders for document sections."""

from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.document_recipes import (
    HEADER_SECTION,
    TASK_VARIANTS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.entities.document import WORK_SOURCE_TYPE
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
    def __init__(self, get_work_source=None):
        self.get_work_source = get_work_source or _get_work_source

    def build_payload(self, request):
        work = self.get_work_source(request.source.source_id)
        variants = [
            _work_variant_payload(variant)
            for variant in work.variant_set.order_by('number', 'pk')
        ]
        return {
            **dict(request.section.options),
            'variants': variants,
        }


def build_work_section_payload_builder_registry(
    get_work_source=None,
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
        DjangoWorkTaskVariantsPayloadBuilder(get_work_source=get_work_source),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    return registry


def _get_work_source(work_id):
    return Work.objects.get(pk=work_id)


def _work_variant_payload(variant):
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
            _variant_task_payload(variant_task)
            for variant_task in variant_tasks
        ],
    }


def _variant_task_payload(variant_task):
    task = variant_task.task
    return {
        **_task_payload(task),
        'order': variant_task.order,
        'max_points': variant_task.max_points,
    }


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
