from django.test import TestCase

from infrastructure.tests.variant_task_factory import create_variant_task

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.entities.work import (
    RemedialContentBlockRow,
    RemedialOriginalTaskRow,
    RemedialSheetData,
    VariantDetailStudentRef,
)
from core_logic.entities.work_document import WorkDocumentSource
from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    HEADER_SECTION,
    ANSWER_KEY_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_DEMO,
    TASK_BANK_ROLE_PRACTICE,
    TASK_RENDER_MODE_TASK_ONLY,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from core_logic.value_objects.variant_print_plan import (
    VARIANT_PRINT_BLOCK_BLANK_CELLS,
    VARIANT_PRINT_BLOCK_TASK,
    VARIANT_PRINT_BLOCK_TEXT,
    VARIANT_PRINT_BLOCK_THEORY,
)
from curriculum.models import SubTopic, Topic
from infrastructure.services.django_document_payload_registry import (
    build_remedial_sheet_section_payload_builder_registry,
    build_work_section_payload_builder_registry,
)
from infrastructure.services.remedial_document_payloads import (
    RemedialSheetDataProvider,
)
from infrastructure.services.work_document_payloads import (
    WorkHeaderPayloadBuilder,
    WorkTaskListPayloadBuilder,
    WorkDocumentSourceProvider,
)
from infrastructure.repositories.django_work_document_repo import (
    DjangoWorkDocumentRepository,
)
from tasks.models import Source, Task
from task_groups.models import AnalogGroup
from works.models import (
    Variant,
    VariantContentBlockSnapshot,
    Work,
    WorkAnalogGroup,
)


class DjangoWorkHeaderPayloadBuilderTests(TestCase):
    def test_work_source_provider_caches_only_in_build_context(self):
        calls = []
        work = object()
        provider = WorkDocumentSourceProvider(
            get_work_document_source=(
                lambda work_id: calls.append(work_id) or work
            ),
        )
        first_build_context = {}

        self.assertIs(provider.get('work-1', first_build_context), work)
        self.assertIs(provider.get('work-1', first_build_context), work)
        self.assertIs(provider.get('work-1', {}), work)

        self.assertEqual(calls, ['work-1', 'work-1'])

    def test_builds_work_header_payload(self):
        work = Work.objects.create(
            name='Контрольная',
            work_type='test',
            duration=60,
            max_score=12,
        )
        builder = WorkHeaderPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
        )

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

    def test_derives_work_header_score_from_assessable_specification(self):
        work = Work.objects.create(
            name='Рабочий лист',
            max_score=0,
        )
        demo_group = AnalogGroup.objects.create(name='Разбор')
        practice_group = AnalogGroup.objects.create(name='Практика')
        WorkAnalogGroup.objects.create(
            work=work,
            analog_group=demo_group,
            count=2,
            weight=5,
            is_assessable=False,
        )
        WorkAnalogGroup.objects.create(
            work=work,
            analog_group=practice_group,
            count=3,
            weight=4,
            is_assessable=True,
        )

        payload = WorkHeaderPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
        ).build_payload(
            build_request(work, HEADER_SECTION),
        )

        self.assertEqual(payload['max_score'], 12)


class DjangoWorkTaskListPayloadBuilderTests(TestCase):
    def test_builds_mixed_variant_content_from_immutable_snapshots(self):
        work = Work.objects.create(name='Рабочий лист')
        variant = Variant.objects.create(work=work, number=1)
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        task = Task.objects.create(
            text='Решите задачу',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        variant_task = create_variant_task(
            variant=variant,
            task=task,
            source_selection_id='selection-1',
            content_order=20,
            order=1,
        )
        theory = VariantContentBlockSnapshot.objects.create(
            variant=variant,
            source_content_id='content-theory',
            content_type='theory',
            order=10,
            title='Опорная теория',
            content={
                'topics': [
                    {
                        'name': 'Динамика',
                        'content': 'Сила изменяет скорость.',
                        'subtopics': [],
                    },
                ],
            },
        )
        VariantContentBlockSnapshot.objects.create(
            variant=variant,
            source_content_id='content-text',
            content_type='text',
            order=30,
            title='Самопроверка',
            content={'body': 'Проверьте единицы измерения.'},
        )
        formatter = FakeTaskPayloadFormatter()
        builder = WorkTaskListPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
            task_payload_formatter=formatter,
        )

        payload = builder.build_payload(
            build_request(work, TASK_LIST_SECTION),
        )

        blocks = payload['variants'][0]['print_blocks']
        self.assertEqual(
            [block['block_type'] for block in blocks],
            [
                VARIANT_PRINT_BLOCK_THEORY,
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_TEXT,
            ],
        )
        self.assertEqual(blocks[0]['snapshot_id'], str(theory.pk))
        self.assertEqual(blocks[0]['title'], 'Опорная теория')
        self.assertEqual(
            blocks[0]['content']['topics'][0]['content'],
            'Сила изменяет скорость.',
        )
        self.assertEqual(
            blocks[1]['task']['variant_task_id'],
            str(variant_task.pk),
        )
        self.assertEqual(
            blocks[2]['content']['body'],
            'Проверьте единицы измерения.',
        )
        formatted_texts = [
            request.get('text')
            for request in formatter.requests
        ]
        self.assertIn('Сила изменяет скорость.', formatted_texts)
        self.assertIn('Проверьте единицы измерения.', formatted_texts)

        task.text = 'Изменённое условие в банке'
        task.answer = 'Изменённый ответ'
        task.save(update_fields=['text', 'answer'])
        frozen_payload = builder.build_payload(
            build_request(work, TASK_LIST_SECTION),
        )
        frozen_task = frozen_payload['variants'][0]['tasks'][0]

        self.assertEqual(frozen_task['text'], 'Решите задачу')
        self.assertEqual(frozen_task['answer'], 'Ответ')

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
        variant_task = create_variant_task(
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
        demo_variant_task = create_variant_task(
            variant=variant,
            task=demo_task,
            source_selection_id='selection-demo',
            order=2,
            max_points=0,
            bank_role=TASK_BANK_ROLE_DEMO,
            render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            is_assessable=False,
            blank_cells_after=True,
            blank_cells_rows=7,
        )
        builder = WorkTaskListPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
        )

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
            [
                task_payload['variant_task_id']
                for task_payload in variant_payload['tasks']
            ],
            [str(variant_task.pk), str(demo_variant_task.pk)],
        )
        self.assertFalse(
            variant_payload['tasks'][1]['is_assessable'],
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
            variant_payload['print_blocks'][1]['source_selection_id'],
            'selection-demo',
        )
        self.assertEqual(
            variant_payload['print_blocks'][1]['task'][
                'source_selection_id'
            ],
            'selection-demo',
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
        create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )
        formatter = FakeTaskPayloadFormatter()
        builder = WorkTaskListPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
            task_payload_formatter=formatter,
        )

        payload = builder.build_payload(build_request(work, TASK_LIST_SECTION))

        task_payload = payload['variants'][0]['tasks'][0]
        self.assertTrue(task_payload['formatted'])
        self.assertEqual(formatter.requests[0]['text'], 'Найдите силу')

    def test_reuses_variant_payload_for_identical_section_inputs(self):
        work = Work.objects.create(name='Контрольная')
        Variant.objects.create(work=work, number=1)
        variant_payload_builder = FakeVariantPayloadBuilder()
        builder = WorkTaskListPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
            variant_payload_builder=variant_payload_builder,
        )
        build_context = {}

        first_payload = builder.build_payload(
            build_request(
                work,
                TASK_LIST_SECTION,
                build_context=build_context,
            )
        )
        second_payload = builder.build_payload(
            build_request(
                work,
                ANSWERS_SECTION,
                build_context=build_context,
            )
        )
        builder.build_payload(
            build_request(
                work,
                TASK_LIST_SECTION,
                options={'hidden_content_types': ['theory']},
                build_context=build_context,
            )
        )
        builder.build_payload(
            build_request(
                work,
                TASK_LIST_SECTION,
                build_context={},
            )
        )

        self.assertIs(first_payload, second_payload)
        self.assertEqual(len(variant_payload_builder.requests), 3)

    def test_task_list_section_options_cannot_override_snapshot_tasks(self):
        work = Work.objects.create(name='Рабочий лист', duration=45)
        variant = Variant.objects.create(work=work, number=1)
        task = self.create_task(
            text='Разберите пример',
            full_solution='Полное решение',
        )
        variant_task = create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=0,
            bank_role=TASK_BANK_ROLE_DEMO,
            render_mode=TASK_RENDER_MODE_TASK_ONLY,
            is_assessable=False,
        )
        builder = WorkTaskListPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
        )

        payload = builder.build_payload(
            build_request(
                work,
                TASK_LIST_SECTION,
                options={
                    'role_render_modes': {
                        TASK_BANK_ROLE_DEMO: (
                            TASK_RENDER_MODE_WITH_FULL_SOLUTION
                        ),
                    },
                    'role_blank_cells': {
                        TASK_BANK_ROLE_DEMO: {'rows': 5},
                    },
                },
            ),
        )

        variant_payload = payload['variants'][0]
        self.assertEqual(
            variant_payload['tasks'][0]['render_mode'],
            TASK_RENDER_MODE_TASK_ONLY,
        )
        self.assertEqual(
            variant_payload['print_blocks'][0]['task']['render_mode'],
            TASK_RENDER_MODE_TASK_ONLY,
        )
        self.assertEqual(
            variant_payload['print_blocks'][0]['content_role'],
            TASK_BANK_ROLE_DEMO,
        )
        self.assertEqual(
            variant_payload['print_blocks'][0]['source_render_mode'],
            TASK_RENDER_MODE_TASK_ONLY,
        )
        self.assertEqual(
            variant_payload['print_blocks'][0]['render_mode'],
            TASK_RENDER_MODE_TASK_ONLY,
        )
        self.assertEqual(len(variant_payload['print_blocks']), 1)

    def test_legacy_hidden_roles_do_not_remove_snapshot_tasks(self):
        work = Work.objects.create(name='Рабочий лист', duration=45)
        variant = Variant.objects.create(work=work, number=1)
        task = self.create_task(text='Самостоятельная задача')
        variant_task = create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=3,
            bank_role=TASK_BANK_ROLE_PRACTICE,
            is_assessable=True,
        )
        builder = WorkTaskListPayloadBuilder(
            work_document_repo=DjangoWorkDocumentRepository(),
        )

        payload = builder.build_payload(
            build_request(
                work,
                TASK_LIST_SECTION,
                options={'hidden_roles': [TASK_BANK_ROLE_PRACTICE]},
            ),
        )

        variant_payload = payload['variants'][0]
        self.assertEqual(
            [task['variant_task_id'] for task in variant_payload['tasks']],
            [str(variant_task.pk)],
        )
        self.assertEqual(
            [
                block['variant_task_id']
                for block in variant_payload['print_blocks']
                if block['block_type'] == 'task'
            ],
            [str(variant_task.pk)],
        )

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

    def test_registry_loads_work_once_per_document_build(self):
        work = Work.objects.create(name='Контрольная')
        calls = []
        work_source = WorkDocumentSource(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            duration=work.duration,
            max_score=work.max_score,
        )
        registry = build_work_section_payload_builder_registry(
            get_work_document_source=(
                lambda work_id: calls.append(work_id) or work_source
            ),
        )
        builder = RecipeDocumentBuilder(
            section_payload_builder_registry=registry,
        )
        source = DocumentSourceRef(
            source_type=WORK_SOURCE_TYPE,
            source_id=str(work.pk),
            title=work.name,
        )
        recipe = DocumentRecipe(
            document_type=WORK_DOCUMENT_TYPE,
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=ANSWERS_SECTION),
            ],
        )

        builder.build(source, recipe)
        builder.build(source, recipe)

        self.assertEqual(calls, [str(work.pk), str(work.pk)])

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

    def test_registry_supports_answer_key_section(self):
        work = Work.objects.create(name='Контрольная')
        registry = build_work_section_payload_builder_registry()

        answer_key_payload = registry.build_payload(
            build_request(work, ANSWER_KEY_SECTION)
        )

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


class DjangoWorkTechnicalPayloadBuilderTests(TestCase):
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
        self.assertEqual(payload['css_max_width'], 54)
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
        variant_task = create_variant_task(
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

    def test_builds_remedial_training_print_plan_from_task_snapshots(self):
        remedial_work = Work.objects.create(name='Работа над ошибками')
        variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
        )
        first_task = self.create_task(text='Первое задание')
        second_task = self.create_task(
            text='Второе задание',
            answer='Ответ',
        )
        first_variant_task = create_variant_task(
            variant=variant,
            task=first_task,
            order=1,
            content_order=20,
            max_points=2,
        )
        second_variant_task = create_variant_task(
            variant=variant,
            task=second_task,
            order=2,
            content_order=10,
            max_points=3,
            render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            blank_cells_after=True,
            blank_cells_rows=7,
        )
        sheet_data = RemedialSheetData(
            variant=variant,
            student=None,
            source_work=None,
            mark=None,
            new_tasks=[first_variant_task, second_variant_task],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
        )
        recipe = remedial_recipe(TRAINING_TASKS_SECTION)

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(
            [
                block['block_type']
                for block in payload['print_blocks']
            ],
            [
                VARIANT_PRINT_BLOCK_TASK,
                VARIANT_PRINT_BLOCK_BLANK_CELLS,
                VARIANT_PRINT_BLOCK_TASK,
            ],
        )
        self.assertEqual(
            payload['print_blocks'][0]['variant_task_id'],
            str(second_variant_task.pk),
        )
        self.assertEqual(
            payload['print_blocks'][0]['task']['render_mode'],
            TASK_RENDER_MODE_WITH_FULL_SOLUTION,
        )
        self.assertEqual(
            payload['print_blocks'][1]['blank_cells']['rows'],
            7,
        )
        self.assertEqual(
            payload['print_blocks'][2]['variant_task_id'],
            str(first_variant_task.pk),
        )

    def test_remedial_print_override_can_hide_snapshot_blank_cells(self):
        remedial_work = Work.objects.create(name='Работа над ошибками')
        variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
        )
        task = self.create_task(text='Задание с клетками')
        variant_task = create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=2,
            blank_cells_after=True,
            blank_cells_rows=6,
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
        recipe = remedial_recipe(
            TRAINING_TASKS_SECTION,
            options={'hide_blank_cells': True},
        )

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(
            [block['block_type'] for block in payload['print_blocks']],
            [VARIANT_PRINT_BLOCK_TASK],
        )
        self.assertTrue(payload['tasks'][0]['blank_cells_after'])

    def test_remedial_print_plan_includes_frozen_static_content(self):
        remedial_work = Work.objects.create(name='Работа над ошибками')
        variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
        )
        task = self.create_task(text='Тренировочное задание')
        variant_task = create_variant_task(
            variant=variant,
            task=task,
            order=1,
            content_order=20,
            max_points=2,
        )
        sheet_data = RemedialSheetData(
            variant=variant,
            student=None,
            source_work=None,
            mark=None,
            new_tasks=[variant_task],
            content_blocks=[
                RemedialContentBlockRow(
                    pk='block-1',
                    source_content_id='source-1',
                    content_type='text',
                    order=10,
                    title='Перед началом',
                    content={'body': 'Вспомните правило.'},
                ),
            ],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
        )
        recipe = remedial_recipe(TRAINING_TASKS_SECTION)

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(
            [block['block_type'] for block in payload['print_blocks']],
            [VARIANT_PRINT_BLOCK_TEXT, VARIANT_PRINT_BLOCK_TASK],
        )
        self.assertEqual(
            payload['print_blocks'][0]['content']['body'],
            'Вспомните правило.',
        )

    def test_remedial_print_override_can_hide_frozen_static_content(self):
        sheet_data = RemedialSheetData(
            variant='variant-1',
            student=None,
            source_work=None,
            mark=None,
            content_blocks=[
                RemedialContentBlockRow(
                    pk='block-1',
                    source_content_id='source-1',
                    content_type='theory',
                    order=10,
                    title='Теория',
                    content={'topics': []},
                ),
            ],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
        )
        recipe = remedial_recipe(
            TRAINING_TASKS_SECTION,
            options={'hidden_content_types': ['theory']},
        )

        payload = registry.build_payload(
            remedial_build_request(
                recipe=recipe,
                section=recipe.sections[0],
            )
        )

        self.assertEqual(payload['print_blocks'], [])
        self.assertEqual(len(sheet_data.content_blocks), 1)

    def test_reuses_remedial_training_payload_for_identical_inputs(self):
        remedial_work = Work.objects.create(name='Работа над ошибками')
        variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
        )
        task = self.create_task(text='Новое задание')
        variant_task = create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=2,
        )
        formatter = FakeTaskPayloadFormatter()
        sheet_data = RemedialSheetData(
            variant=variant,
            student=None,
            source_work=None,
            mark=None,
            new_tasks=[variant_task],
        )
        registry = build_remedial_sheet_section_payload_builder_registry(
            get_remedial_sheet_data=lambda variant_id: sheet_data,
            task_payload_formatter=formatter,
        )
        build_context = {}
        training_recipe = remedial_recipe(TRAINING_TASKS_SECTION)
        answers_recipe = remedial_recipe(ANSWERS_SECTION)

        first_payload = registry.build_payload(
            remedial_build_request(
                recipe=training_recipe,
                section=training_recipe.sections[0],
                build_context=build_context,
            )
        )
        second_payload = registry.build_payload(
            remedial_build_request(
                recipe=answers_recipe,
                section=answers_recipe.sections[0],
                build_context=build_context,
            )
        )
        distinct_recipe = remedial_recipe(
            TRAINING_TASKS_SECTION,
            options={'include_scores': False},
        )
        registry.build_payload(
            remedial_build_request(
                recipe=distinct_recipe,
                section=distinct_recipe.sections[0],
                build_context=build_context,
            )
        )
        registry.build_payload(
            remedial_build_request(
                recipe=training_recipe,
                section=training_recipe.sections[0],
                build_context={},
            )
        )

        self.assertIs(first_payload, second_payload)
        self.assertEqual(len(formatter.requests), 3)

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

    def test_provider_caches_sheet_data_only_in_build_context(self):
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
        first_build_context = {}

        self.assertEqual(
            provider.get('variant-1', first_build_context),
            sheet_data,
        )
        self.assertEqual(
            provider.get('variant-1', first_build_context),
            sheet_data,
        )
        self.assertEqual(provider.get('variant-1', {}), sheet_data)

        self.assertEqual(calls, ['variant-1', 'variant-1'])

    def test_provider_requires_data_loader(self):
        with self.assertRaisesRegex(
            ValueError,
            'get_remedial_sheet_data is required',
        ):
            RemedialSheetDataProvider()

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


class FakeVariantPayloadBuilder:
    def __init__(self):
        self.requests = []

    def build(self, variant, request=None):
        self.requests.append((variant, request))
        return {'id': str(variant.pk)}


def remedial_recipe(section_type, options=None):
    return DocumentRecipe(
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        sections=[
            DocumentSectionSpec(
                section_type=section_type,
                options=options or {},
            )
        ],
    )


def remedial_build_request(
    recipe,
    section,
    build_context=None,
):
    return DocumentSectionPayloadBuildRequest(
        source=DocumentSourceRef(
            source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
            source_id='variant-1',
            title='Разбор',
        ),
        recipe=recipe,
        section=section,
        build_context=(
            build_context
            if build_context is not None
            else {}
        ),
    )


def build_request(
    work,
    section_type,
    options=None,
    build_context=None,
):
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
        build_context=(
            build_context
            if build_context is not None
            else {}
        ),
    )
