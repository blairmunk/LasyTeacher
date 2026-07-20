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
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    TASK_VARIANTS_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from curriculum.models import SubTopic, Topic
from infrastructure.services.django_document_section_payloads import (
    DjangoWorkHeaderPayloadBuilder,
    DjangoWorkTaskVariantsPayloadBuilder,
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


class DjangoWorkTaskVariantsPayloadBuilderTests(TestCase):
    def test_builds_task_variants_payload(self):
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
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )
        builder = DjangoWorkTaskVariantsPayloadBuilder()

        payload = builder.build_payload(
            build_request(
                work,
                TASK_VARIANTS_SECTION,
                options={'include_hints': True},
            ),
        )

        self.assertTrue(payload['include_hints'])
        self.assertEqual(len(payload['variants']), 1)
        variant_payload = payload['variants'][0]
        self.assertEqual(variant_payload['number'], 2)
        self.assertEqual(variant_payload['max_score'], 8)
        self.assertEqual(variant_payload['duration'], 40)
        self.assertEqual(len(variant_payload['tasks']), 1)
        task_payload = variant_payload['tasks'][0]
        self.assertEqual(task_payload['order'], 1)
        self.assertEqual(task_payload['max_points'], 4)
        self.assertEqual(task_payload['text'], 'Найдите силу')
        self.assertEqual(task_payload['answer'], '10 Н')
        self.assertEqual(task_payload['topic'], 'Динамика')
        self.assertEqual(task_payload['subtopic'], 'Силы')
        self.assertEqual(task_payload['source'], 'Сб.')
        self.assertEqual(task_payload['source_detail'], 'стр. 10')

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

    def test_registry_supports_legacy_work_section_names(self):
        work = Work.objects.create(name='Контрольная')
        registry = build_work_section_payload_builder_registry()

        task_list_payload = registry.build_payload(
            build_request(work, TASK_LIST_SECTION)
        )
        answer_key_payload = registry.build_payload(
            build_request(work, ANSWER_KEY_SECTION)
        )

        self.assertEqual(task_list_payload['variants'], [])
        self.assertEqual(answer_key_payload['variants'], [])


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
