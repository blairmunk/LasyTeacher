"""Django-backed payload builders for document sections."""

from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    COMMON_HEADER_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    LEGACY_ANSWER_KEY_SECTION,
    LEGACY_TASK_VARIANTS_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    THEORY_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.entities.document import (
    REMEDIAL_WORK_SOURCE_TYPE,
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
        block_payload['content'] = _format_text_payload(
            block_payload['content'],
            self.task_payload_formatter,
            request=request,
        )
        block_payload['subtopics'] = [
            {
                **subtopic,
                'content': _format_text_payload(
                    subtopic['content'],
                    self.task_payload_formatter,
                    request=request,
                ),
            }
            for subtopic in block_payload['subtopics']
        ]
        return block_payload


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
        sheet_data = self.sheet_data_provider.get(_remedial_variant_id(request))
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
        sheet_data = self.sheet_data_provider.get(_remedial_variant_id(request))
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
        sheet_data = self.sheet_data_provider.get(_remedial_variant_id(request))
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


class BlankCellsPayloadBuilder:
    def build_payload(self, request):
        options = dict(request.section.options)
        rows = _positive_int(options.get('rows'), default=6, max_value=40)
        columns = _positive_int(
            options.get('columns'),
            default=24,
            max_value=40,
        )
        row_height = _positive_int(
            options.get('row_height'),
            default=24,
            max_value=120,
        )
        return {
            **options,
            'rows': rows,
            'columns': columns,
            'row_height': row_height,
            'rows_range': range(rows),
            'cells_range': range(rows * columns),
            'latex_cells': _blank_cells_latex_cells(columns, row_height),
        }


def build_work_section_payload_builder_registry(
    get_work_source=None,
    task_payload_formatter=None,
) -> DocumentSectionPayloadBuilderRegistry:
    registry = DocumentSectionPayloadBuilderRegistry()
    task_list_builder = DjangoWorkTaskListPayloadBuilder(
        get_work_source=get_work_source,
        task_payload_formatter=task_payload_formatter,
    )
    registry.register(
        COMMON_HEADER_SECTION,
        DjangoWorkHeaderPayloadBuilder(get_work_source=get_work_source),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        HEADER_SECTION,
        DjangoWorkHeaderPayloadBuilder(get_work_source=get_work_source),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        TASK_LIST_SECTION,
        task_list_builder,
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        LEGACY_TASK_VARIANTS_SECTION,
        task_list_builder,
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        THEORY_SECTION,
        DjangoWorkTheoryPayloadBuilder(
            get_work_source=get_work_source,
            task_payload_formatter=task_payload_formatter,
        ),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        BLANK_CELLS_SECTION,
        BlankCellsPayloadBuilder(),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    for section_type in (
        ANSWERS_SECTION,
        LEGACY_ANSWER_KEY_SECTION,
        SHORT_SOLUTIONS_SECTION,
        FULL_SOLUTIONS_SECTION,
    ):
        registry.register(
            section_type,
            task_list_builder,
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
    header_builder = DjangoRemedialHeaderPayloadBuilder(sheet_data_provider)
    original_mistakes_builder = DjangoRemedialOriginalMistakesPayloadBuilder(
        sheet_data_provider,
        task_payload_formatter=task_payload_formatter,
    )
    training_tasks_builder = DjangoRemedialTrainingTasksPayloadBuilder(
        sheet_data_provider,
        task_payload_formatter=task_payload_formatter,
    )
    blank_cells_builder = BlankCellsPayloadBuilder()
    for source_type in (REMEDIAL_VARIANT_SOURCE_TYPE, REMEDIAL_WORK_SOURCE_TYPE):
        registry.register(
            HEADER_SECTION,
            header_builder,
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=source_type,
        )
        registry.register(
            ORIGINAL_MISTAKES_SECTION,
            original_mistakes_builder,
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=source_type,
        )
        registry.register(
            BLANK_CELLS_SECTION,
            blank_cells_builder,
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=source_type,
        )
    for section_type in (
        TRAINING_TASKS_SECTION,
        ANSWERS_SECTION,
        SHORT_SOLUTIONS_SECTION,
        FULL_SOLUTIONS_SECTION,
    ):
        for source_type in (
            REMEDIAL_VARIANT_SOURCE_TYPE,
            REMEDIAL_WORK_SOURCE_TYPE,
        ):
            registry.register(
                section_type,
                training_tasks_builder,
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                source_type=source_type,
            )
    return registry


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


def _remedial_variant_id(request):
    return request.section.options.get('variant_id') or request.source.source_id


def _positive_int(value, default, max_value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    return min(parsed, max_value)


def _blank_cells_latex_cells(columns, row_height):
    cells = [''] * columns
    cells[0] = rf'\rule{{0pt}}{{{row_height / 3:.1f}mm}}'
    return cells


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


def _format_text_payload(text, task_payload_formatter=None, request=None):
    if task_payload_formatter is None:
        return text
    return task_payload_formatter.format_task_payload(
        {'text': text},
        request=request,
    )['text']


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
