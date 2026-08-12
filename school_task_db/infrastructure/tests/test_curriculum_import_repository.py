from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry
from core_logic.entities.curriculum_import import (
    CodifierContentBindingItem,
    CurriculumImportDefinition,
    CurriculumImportRequest,
    CurriculumSubtopicImportItem,
    CurriculumTopicImportItem,
)
from curriculum.models import SubTopic, Topic
from infrastructure.container import Container
from infrastructure.repositories.django_curriculum_import_repo import (
    DjangoCurriculumImportRepository,
)


def _definition(binding_code='1.1'):
    return CurriculumImportDefinition(
        subject='Физика',
        sections=('Механика',),
        topics=(
            CurriculumTopicImportItem(
                section='Механика',
                name='Кинематика',
                grade_level=9,
                order=2,
                subtopics=(
                    CurriculumSubtopicImportItem('Скорость', 1),
                ),
            ),
        ),
        bindings=(
            CodifierContentBindingItem(
                codifier_short_name='ОГЭ 2026',
                content_code=binding_code,
                topic_name='Кинематика',
                subtopic_name='Скорость',
            ),
        ),
    )


class DjangoCurriculumImportRepositoryTests(TestCase):
    def setUp(self):
        codifier = CodifierSpec.objects.create(
            name='ОГЭ 2026 по физике',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        self.entry = ContentEntry.objects.create(
            codifier=codifier,
            code='1.1',
            name='Скорость',
        )

    def test_container_imports_topics_and_applies_binding(self):
        result = Container().import_curriculum_use_case().execute(
            CurriculumImportRequest(definition=_definition()),
        )

        self.entry.refresh_from_db()
        self.assertEqual(result.topics_created, 1)
        self.assertEqual(result.subtopics_created, 1)
        self.assertEqual(result.bindings_applied, 1)
        self.assertEqual(self.entry.topic.name, 'Кинематика')
        self.assertEqual(self.entry.subtopic.name, 'Скорость')
        self.assertEqual(result.bound_codifier_entries, 1)
        self.assertEqual(result.total_codifier_entries, 1)

    def test_missing_codifier_entry_is_returned_as_issue(self):
        result = Container().import_curriculum_use_case().execute(
            CurriculumImportRequest(definition=_definition('missing')),
        )

        self.assertEqual(result.bindings_applied, 0)
        self.assertEqual(result.issues[0].reason, 'entry_not_found')
        self.assertEqual(result.issues[0].content_code, 'missing')

    def test_clear_only_replaces_matching_subject_topics(self):
        old_physics = Topic.objects.create(
            name='Старая физика',
            subject='Физика',
            section='Механика',
            grade_level=7,
        )
        SubTopic.objects.create(topic=old_physics, name='Старая подтема')
        chemistry = Topic.objects.create(
            name='Механика молекул',
            subject='Химия',
            section='Механика',
            grade_level=8,
        )

        result = Container().import_curriculum_use_case().execute(
            CurriculumImportRequest(
                definition=_definition(),
                clear_existing=True,
            ),
        )

        self.assertEqual(result.topics_deleted, 1)
        self.assertEqual(result.subtopics_deleted, 1)
        self.assertFalse(Topic.objects.filter(pk=old_physics.pk).exists())
        self.assertTrue(Topic.objects.filter(pk=chemistry.pk).exists())

    def test_container_wires_curriculum_import_adapter(self):
        use_case = Container().import_curriculum_use_case()

        self.assertIsInstance(
            use_case.curriculum_repo,
            DjangoCurriculumImportRepository,
        )
