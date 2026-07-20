from django.test import TestCase

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    TASK_VARIANTS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from curriculum.models import SubTopic, Topic
from infrastructure.services.django_document_section_payloads import (
    DjangoWorkHeaderPayloadBuilder,
    DjangoWorkTaskVariantsPayloadBuilder,
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
