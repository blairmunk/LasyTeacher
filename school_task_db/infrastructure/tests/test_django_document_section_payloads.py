from django.test import TestCase

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.entities.work import (
    RemedialOriginalTaskRow,
    RemedialSheetData,
    VariantDetailStudentRef,
)
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    HEADER_SECTION,
    LEGACY_ANSWER_KEY_SECTION,
    LEGACY_TASK_VARIANTS_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    THEORY_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.variant_print_plan import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_DEMO,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
    VARIANT_PRINT_BLOCK_BLANK_CELLS,
    VARIANT_PRINT_BLOCK_TASK,
)
from curriculum.models import SubTopic, Topic
from infrastructure.services.django_document_section_payloads import (
    DjangoWorkHeaderPayloadBuilder,
    DjangoWorkTaskListPayloadBuilder,
    DjangoWorkTheoryPayloadBuilder,
    RemedialSheetDataProvider,
    build_remedial_sheet_section_payload_builder_registry,
    build_work_section_payload_builder_registry,
)
from tasks.models import Source, Task
from works.models import Variant, VariantTask, Work


class DjangoWorkHeaderPayloadBuilderTests(TestCase):
    def test_builds_work_header_payload(self):
        work = Work.objects.create(
            name='Контрольная',
            work_type='test',
            duration=60,
            max_score=12,
        )
        builder = DjangoWorkHeaderPayloadBuilder()

        payload = builder.build_payload(
            build_request(work, HEADER_SECTION, options={'show_date': True}),
        )

        self.assertEqual(
            payload,
            {
                'show_date': True,
                'title': 'Контрольная',
                'work_type': 'test',
                'duration': 60,
                'max_score': 12,
            },
        )


class DjangoWorkTaskListPayloadBuilderTests(TestCase):
    def test_builds_task_list_payload(self):
        work = Work.objects.create(name='Контрольная', duration=45)
        variant = Variant.objects.create(
            work=work,
            number=2,
            work_name_snapshot='Контрольная',
            max_score_snapshot=8,
            duration_snapshot=40,
        )
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        subtopic = SubTopic.objects.create(topic=topic, name='Силы')
        source = Source.objects.create(name='Сборник', short_name='Сб.')
        task = Task.objects.create(
            text='Найдите силу',
            answer='10 Н',
            short_solution='F = ma',
            full_solution='Подставляем значения',
            hint='Второй закон Ньютона',
            instruction='Запишите формулу',
            topic=topic,
            subtopic=subtopic,
            task_type='computational',
            difficulty=3,
            source=source,
            source_detail='стр. 10',
        )
        variant_task = VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )
        demo_task = Task.objects.create(
            text='Разберите пример',
            answer='42',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        demo_variant_task = VariantTask.objects.create(
            variant=variant,
            task=demo_task,
            order=2,
            max_points=0,
            bank_role=TASK_BANK_ROLE_DEMO,
            render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            is_assessable=False,
            blank_cells_after=True,
            blank_cells_rows=7,
        )
        builder = DjangoWorkTaskListPayloadBuilder()

        payload = builder.build_payload(
            build_request(
                work,
                TASK_LIST_SECTION,
                options={'include_hints': True},
            ),
        )

        self.assertTrue(payload['include_hints'])
        self.assertEqual(len(payload['variants']), 1)
        variant_payload = payload['variants'][0]
        self.assertEqual(variant_payload['number'], 2)
        self.assertEqual(variant_payload['max_score'], 8)
        self.assertEqual(variant_payload['duration'], 40)
        self.assertEqual(
            variant_payload['assessable_variant_task_ids'],
            (str(variant_task.pk),),
        )
        self.assertEqual(
            variant_payload['content_plan']['assessable_variant_task_ids'],
            (str(variant_task.pk),),
        )
        self.assertEqual(
            [
                item['variant_task_id']
                for item in variant_payload['content_plan']['items']
            ],
            [str(variant_task.pk), str(demo_variant_task.pk)],
        )
        self.assertFalse(
            variant_payload['content_plan']['items'][1]['is_assessable'],
        )
        self.assertEqual(
            [block['block_type'] for block in variant_payload['print_plan']['blocks']],
            [
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_BLANK_CELLS,
            ],
        )
        self.assertEqual(
            variant_payload['print_plan']['blocks'][2]['variant_task_id'],
            str(demo_variant_task.pk),
        )
        self.assertEqual(
            variant_payload['print_plan']['blocks'][2]['options'],
            {'rows': 7},
        )
        self.assertEqual(
            [block['block_type'] for block in variant_payload['print_blocks']],
            [
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_BLANK_CELLS,
            ],
        )
        self.assertEqual(
            variant_payload['print_blocks'][1]['task']['variant_task_id'],
            str(demo_variant_task.pk),
        )
        self.assertEqual(
            variant_payload['print_blocks'][2]['blank_cells']['rows'],
            7,
        )
        self.assertEqual(len(variant_payload['tasks']), 2)
        task_payload = variant_payload['tasks'][0]
        self.assertEqual(task_payload['variant_task_id'], str(variant_task.pk))
        self.assertEqual(task_payload['order'], 1)
        self.assertEqual(task_payload['max_points'], 4)
        self.assertEqual(task_payload['bank_role'], TASK_BANK_ROLE_CONTROL)
        self.assertEqual(task_payload['render_mode'], TASK_RENDER_MODE_TASK_ONLY)
        self.assertTrue(task_payload['is_assessable'])
        self.assertFalse(task_payload['blank_cells_after'])
        self.assertEqual(
            task_payload['blank_cells_rows'],
            DEFAULT_BLANK_CELLS_ROWS,
        )
        self.assertEqual(task_payload['text'], 'Найдите силу')
        self.assertEqual(task_payload['answer'], '10 Н')
        self.assertEqual(task_payload['topic'], 'Динамика')
        self.assertEqual(task_payload['subtopic'], 'Силы')
        self.assertEqual(task_payload['source'], 'Сб.')
        self.assertEqual(task_payload['source_detail'], 'стр. 10')

    def test_builds_task_list_payload_with_task_formatter(self):
        work = Work.objects.create(name='Контрольная', duration=45)
        variant = Variant.objects.create(work=work, number=1)
        task = self.create_task(text='Найдите силу')
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )
        formatter = FakeTaskPayloadFormatter()
        builder = DjangoWorkTaskListPayloadBuilder(
            task_payload_formatter=formatter,
        )

        payload = builder.build_payload(build_request(work, TASK_LIST_SECTION))

        task_payload = payload['variants'][0]['tasks'][0]
        self.assertTrue(task_payload['formatted'])
        self.assertEqual(formatter.requests[0]['text'], 'Найдите силу')

    def test_builds_registry_for_work_sections(self):
        work = Work.objects.create(name='Контрольная')
        registry = build_work_section_payload_builder_registry()
        recipe = DocumentRecipe(
            document_type=WORK_DOCUMENT_TYPE,
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )

        payload = registry.build_payload(
            DocumentSectionPayloadBuildRequest(
                source=DocumentSourceRef(
                    source_type=WORK_SOURCE_TYPE,
                    source_id=str(work.pk),
                    title=work.name,
                ),
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(payload['title'], 'Контрольная')

    def test_registry_uses_variant_payload_for_answer_sections(self):
        work = Work.objects.create(name='Контрольная')
        registry = build_work_section_payload_builder_registry()
        recipe = DocumentRecipe(
            document_type=WORK_DOCUMENT_TYPE,
            sections=[DocumentSectionSpec(section_type=ANSWERS_SECTION)],
        )

        payload = registry.build_payload(
            DocumentSectionPayloadBuildRequest(
                source=DocumentSourceRef(
                    source_type=WORK_SOURCE_TYPE,
                    source_id=str(work.pk),
                    title=work.name,
                ),
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(payload['variants'], [])

    def test_registry_supports_work_section_aliases(self):
        work = Work.objects.create(name='Контрольная')
        registry = build_work_section_payload_builder_registry()

        task_variants_payload = registry.build_payload(
            build_request(work, LEGACY_TASK_VARIANTS_SECTION)
        )
        answer_key_payload = registry.build_payload(
            build_request(work, LEGACY_ANSWER_KEY_SECTION)
        )

        self.assertEqual(task_variants_payload['variants'], [])
        self.assertEqual(answer_key_payload['variants'], [])

    def create_task(self, **overrides):
        topic = Topic.objects.create(
            name=f"Тема {overrides.get('text', '')}",
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        defaults = {
            'text': 'Задание',
            'answer': 'Ответ',
            'topic': topic,
            'task_type': 'computational',
            'difficulty': 2,
        }
        defaults.update(overrides)
        return Task.objects.create(**defaults)


class DjangoWorkTheoryPayloadBuilderTests(TestCase):
    def test_builds_theory_payload_from_work_task_topics(self):
        work = Work.objects.create(name='Контрольная')
        variant = Variant.objects.create(work=work, number=1)
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
            description='Второй закон Ньютона: F = ma',
        )
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        second_task = Task.objects.create(
            text='Второе задание',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        VariantTask.objects.create(variant=variant, task=task, order=1)
        VariantTask.objects.create(variant=variant, task=second_task, order=2)
        builder = DjangoWorkTheoryPayloadBuilder()

        payload = builder.build_payload(build_request(work, THEORY_SECTION))

        self.assertEqual(payload['section_title'], 'Теоретическая справка')
        self.assertEqual(len(payload['blocks']), 1)
        self.assertEqual(payload['blocks'][0]['topic_name'], 'Динамика')
        self.assertEqual(
            payload['blocks'][0]['content'],
            'Второй закон Ньютона: F = ma',
        )

    def test_skips_topics_without_description(self):
        work = Work.objects.create(name='Контрольная')
        variant = Variant.objects.create(work=work, number=1)
        task = self.create_task(description='')
        VariantTask.objects.create(variant=variant, task=task, order=1)
        builder = DjangoWorkTheoryPayloadBuilder()

        payload = builder.build_payload(build_request(work, THEORY_SECTION))

        self.assertEqual(payload['blocks'], [])

    def test_can_include_subtopic_descriptions(self):
        work = Work.objects.create(name='Контрольная')
        variant = Variant.objects.create(work=work, number=1)
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
            description='Теория темы',
        )
        subtopic = SubTopic.objects.create(
            topic=topic,
            name='Силы',
            description='Теория подтемы',
        )
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=topic,
            subtopic=subtopic,
            task_type='computational',
            difficulty=2,
        )
        VariantTask.objects.create(variant=variant, task=task, order=1)
        builder = DjangoWorkTheoryPayloadBuilder()

        payload = builder.build_payload(
            build_request(
                work,
                THEORY_SECTION,
                options={'include_subtopics': True},
            )
        )

        self.assertEqual(payload['blocks'][0]['subtopics'][0]['name'], 'Силы')
        self.assertEqual(
            payload['blocks'][0]['subtopics'][0]['content'],
            'Теория подтемы',
        )

    def test_formats_theory_text_with_task_formatter(self):
        work = Work.objects.create(name='Контрольная')
        variant = Variant.objects.create(work=work, number=1)
        task = self.create_task(description='Закон $F=ma$')
        VariantTask.objects.create(variant=variant, task=task, order=1)
        formatter = FakeTaskPayloadFormatter()
        builder = DjangoWorkTheoryPayloadBuilder(
            task_payload_formatter=formatter,
        )

        payload = builder.build_payload(build_request(work, THEORY_SECTION))

        self.assertEqual(
            payload['blocks'][0]['content'],
            'Закон $F=ma$',
        )
        self.assertEqual(formatter.requests[0]['text'], 'Закон $F=ma$')

    def test_registry_supports_work_theory_section(self):
        work = Work.objects.create(name='Контрольная')
        variant = Variant.objects.create(work=work, number=1)
        task = self.create_task(description='Теория')
        VariantTask.objects.create(variant=variant, task=task, order=1)
        registry = build_work_section_payload_builder_registry()

        payload = registry.build_payload(build_request(work, THEORY_SECTION))

        self.assertEqual(payload['blocks'][0]['content'], 'Теория')

    def test_registry_supports_work_blank_cells_section(self):
        work = Work.objects.create(name='Контрольная')
        registry = build_work_section_payload_builder_registry()

        payload = registry.build_payload(
            build_request(
                work,
                BLANK_CELLS_SECTION,
                options={'rows': '2', 'columns': '3', 'row_height': '18'},
            )
        )

        self.assertEqual(payload['rows'], 2)
        self.assertEqual(payload['columns'], 3)
        self.assertEqual(payload['row_height'], 18)
        self.assertEqual(list(payload['rows_range']), [0, 1])
        self.assertEqual(list(payload['cells_range']), [0, 1, 2, 3, 4, 5])

    def create_task(self, description='Теория темы', **overrides):
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
            description=description,
        )
        defaults = {
            'text': 'Задание',
            'answer': 'Ответ',
            'topic': topic,
            'task_type': 'computational',
            'difficulty': 2,
        }
        defaults.update(overrides)
        return Task.objects.create(**defaults)


class DjangoRemedialSectionPayloadBuilderTests(TestCase):
    def test_builds_remedial_header_payload(self):
        source_work = Work.objects.create(name='Исходная работа')
        sheet_data = RemedialSheetData(
            variant='variant',
            student=VariantDetailStudentRef(
                pk='student-1',
                full_name='Петров Пётр',
                short_name='Петров П.',
            ),
            source_work=source_work,
            mark=FakeMark(score=3, points=2, max_points=5),
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
        )
        recipe = remedial_recipe(HEADER_SECTION)

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(payload['title'], 'Работа над ошибками')
        self.assertEqual(
            payload['student'],
            {
                'id': 'student-1',
                'full_name': 'Петров Пётр',
                'short_name': 'Петров П.',
            },
        )
        self.assertEqual(
            payload['source_work'],
            {'id': str(source_work.pk), 'name': 'Исходная работа'},
        )
        self.assertEqual(
            payload['mark'],
            {'score': 3, 'points': 2, 'max_points': 5},
        )

    def test_builds_remedial_original_mistakes_payload(self):
        task = self.create_task(text='Исходное задание', answer='Ответ')
        sheet_data = RemedialSheetData(
            variant='variant',
            student=None,
            source_work=None,
            mark=None,
            original_tasks=[
                RemedialOriginalTaskRow(
                    task=task,
                    order=1,
                    points=2,
                    max_points=5,
                    pct=40.0,
                    status='partial',
                    group_name='Движение',
                ),
            ],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
        )
        recipe = remedial_recipe(ORIGINAL_MISTAKES_SECTION)

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(len(payload['tasks']), 1)
        task_payload = payload['tasks'][0]
        self.assertEqual(task_payload['order'], 1)
        self.assertEqual(task_payload['text'], 'Исходное задание')
        self.assertEqual(task_payload['points'], 2)
        self.assertEqual(task_payload['max_points'], 5)
        self.assertEqual(task_payload['pct'], 40.0)
        self.assertEqual(task_payload['status'], 'partial')
        self.assertEqual(task_payload['group_name'], 'Движение')

    def test_builds_remedial_training_and_answer_payload_from_new_tasks(self):
        remedial_work = Work.objects.create(name='Работа над ошибками')
        variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
        )
        task = self.create_task(
            text='Новое задание',
            answer='Новый ответ',
            short_solution='Краткое решение',
        )
        variant_task = VariantTask.objects.create(
            variant=variant,
            task=task,
            order=2,
            max_points=3,
        )
        sheet_data = RemedialSheetData(
            variant=variant,
            student=None,
            source_work=None,
            mark=None,
            new_tasks=[variant_task],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
        )
        recipe = remedial_recipe(ANSWERS_SECTION)

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(len(payload['tasks']), 1)
        task_payload = payload['tasks'][0]
        self.assertEqual(task_payload['order'], 2)
        self.assertEqual(task_payload['max_points'], 3)
        self.assertEqual(task_payload['text'], 'Новое задание')
        self.assertEqual(task_payload['answer'], 'Новый ответ')
        self.assertEqual(task_payload['short_solution'], 'Краткое решение')

    def test_builds_remedial_payload_with_task_formatter(self):
        task = self.create_task(text='Исходное задание', answer='Ответ')
        formatter = FakeTaskPayloadFormatter()
        sheet_data = RemedialSheetData(
            variant='variant',
            student=None,
            source_work=None,
            mark=None,
            original_tasks=[
                RemedialOriginalTaskRow(
                    task=task,
                    order=1,
                    points=2,
                    max_points=5,
                    pct=40.0,
                    status='partial',
                    group_name='Движение',
                ),
            ],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
            task_payload_formatter=formatter,
        )
        recipe = remedial_recipe(ORIGINAL_MISTAKES_SECTION)

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertTrue(payload['tasks'][0]['formatted'])
        self.assertEqual(formatter.requests[0]['text'], 'Исходное задание')

    def test_provider_caches_sheet_data_per_variant(self):
        calls = []
        sheet_data = RemedialSheetData(
            variant='variant',
            student=None,
            source_work=None,
            mark=None,
        )
        provider = RemedialSheetDataProvider(
            get_remedial_sheet_data=lambda variant_id:
                calls.append(variant_id) or sheet_data,
        )

        self.assertEqual(provider.get('variant-1'), sheet_data)
        self.assertEqual(provider.get('variant-1'), sheet_data)

        self.assertEqual(calls, ['variant-1'])

    def create_task(self, **overrides):
        topic = Topic.objects.create(
            name=f"Тема {overrides.get('text', '')}",
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        defaults = {
            'text': 'Задание',
            'answer': 'Ответ',
            'topic': topic,
            'task_type': 'computational',
            'difficulty': 2,
        }
        defaults.update(overrides)
        return Task.objects.create(**defaults)


class FakeMark:
    def __init__(self, score, points, max_points):
        self.score = score
        self.points = points
        self.max_points = max_points


class FakeTaskPayloadFormatter:
    def __init__(self):
        self.requests = []

    def format_task_payload(self, payload, request=None):
        self.requests.append(dict(payload))
        return {
            **payload,
            'formatted': True,
        }


def remedial_recipe(section_type):
    return DocumentRecipe(
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        sections=[DocumentSectionSpec(section_type=section_type)],
    )


def remedial_build_request(recipe, section):
    return DocumentSectionPayloadBuildRequest(
        source=DocumentSourceRef(
            source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
            source_id='variant-1',
            title='Разбор',
        ),
        recipe=recipe,
        section=section,
    )


def build_request(work, section_type, options=None):
    recipe = DocumentRecipe(
        document_type=WORK_DOCUMENT_TYPE,
        sections=[
            DocumentSectionSpec(
                section_type=section_type,
                options=options or {},
            ),
        ],
    )
    return DocumentSectionPayloadBuildRequest(
        source=DocumentSourceRef(
            source_type=WORK_SOURCE_TYPE,
            source_id=str(work.pk),
            title=work.name,
        ),
        recipe=recipe,
        section=recipe.sections[0],
    )
