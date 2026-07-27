"""Django-backed document payload builders for regular works."""

from core_logic.value_objects.document_recipes import (
    TASK_LIST_SECTION,
)
from infrastructure.services.django_variant_document_payloads import (
    DjangoVariantDocumentPayloadBuilder,
    format_text_payload,
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


class DjangoWorkTheoryPayloadBuilder:
    def __init__(self, get_work_source=None, task_payload_formatter=None):
        self.get_work_source = get_work_source or _get_work_source
        self.task_payload_formatter = task_payload_formatter

    def build_payload(self, request):
        work = self.get_work_source(request.source.source_id)
        options = dict(request.section.options)
        include_subtopics = options.get('include_subtopics', False)
        if self._is_embedded_in_variant_content(work, request):
            return {
                **options,
                'section_title': options.get(
                    'section_title',
                    'Теоретическая справка',
                ),
                'blocks': [],
                'embedded_in_variants': True,
            }
        return {
            **options,
            'section_title': options.get(
                'section_title',
                'Теоретическая справка',
            ),
            'blocks': self._topic_blocks(
                work,
                request=request,
                include_subtopics=include_subtopics,
            ),
        }

    def _is_embedded_in_variant_content(self, work, request):
        if TASK_LIST_SECTION not in {
            section.section_type
            for section in request.recipe.sections
        }:
            return False
        return any(
            variant.content_block_snapshots.filter(
                content_type='theory',
            ).exists()
            for variant in _work_variants_from_request(work, request)
        )

    def _topic_blocks(self, work, request=None, include_subtopics=False):
        topic_map = {}
        for variant in _work_variants_from_request(work, request):
            variant_tasks = (
                variant.varianttask_set
                .select_related('task', 'task__topic', 'task__subtopic')
                .order_by('order', 'pk')
            )
            for variant_task in variant_tasks:
                task = variant_task.task
                topic = task.topic
                if not topic or not topic.description:
                    continue
                topic_id = str(topic.pk)
                if topic_id not in topic_map:
                    topic_map[topic_id] = {
                        'id': topic_id,
                        'topic_name': topic.name,
                        'subject': topic.subject,
                        'section': topic.section,
                        'grade_level': topic.grade_level,
                        'content': topic.description,
                        'subtopics': [],
                    }
                if include_subtopics and task.subtopic:
                    subtopic = task.subtopic
                    if subtopic.description:
                        _append_unique_subtopic(
                            topic_map[topic_id]['subtopics'],
                            subtopic,
                        )
        return [
            self._format_block_payload(block, request=request)
            for block in topic_map.values()
        ]

    def _format_block_payload(self, block, request=None):
        block_payload = dict(block)
        block_payload['content'] = format_text_payload(
            block_payload['content'],
            self.task_payload_formatter,
            request=request,
        )
        block_payload['subtopics'] = [
            {
                **subtopic,
                'content': format_text_payload(
                    subtopic['content'],
                    self.task_payload_formatter,
                    request=request,
                ),
            }
            for subtopic in block_payload['subtopics']
        ]
        return block_payload


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


def _append_unique_subtopic(subtopics, subtopic):
    subtopic_id = str(subtopic.pk)
    if any(item['id'] == subtopic_id for item in subtopics):
        return
    subtopics.append(
        {
            'id': subtopic_id,
            'name': subtopic.name,
            'content': subtopic.description,
        }
    )
