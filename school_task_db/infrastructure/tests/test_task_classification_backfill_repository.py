from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry
from core_logic.entities.task_classification_backfill import (
    BackfillTaskClassificationsRequest,
)
from curriculum.models import Topic
from infrastructure.container import Container
from infrastructure.repositories.django_task_classification_backfill_repo import (
    DjangoTaskClassificationBackfillRepository,
)
from tasks.models import Task


class DjangoTaskClassificationBackfillRepositoryTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.task = Task.objects.create(
            text='Найти силу',
            answer='10 Н',
            topic=self.topic,
            content_element='1.1',
            task_type='computational',
            difficulty=2,
        )
        codifier = CodifierSpec.objects.create(
            name='ОГЭ по физике 2026',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        self.entry = ContentEntry.objects.create(
            codifier=codifier,
            code='1.1',
            name='Динамика',
            topic=self.topic,
        )

    def test_preview_does_not_write_and_apply_is_idempotent(self):
        use_case = Container().backfill_task_classifications_use_case()

        preview = use_case.execute(
            BackfillTaskClassificationsRequest(apply=False),
        )

        self.assertEqual(preview.status, 'preview')
        self.assertEqual(preview.plan.content_count, 1)
        self.assertFalse(self.task.codifier_content_entries.exists())

        applied = use_case.execute(
            BackfillTaskClassificationsRequest(apply=True),
        )
        repeated = use_case.execute(
            BackfillTaskClassificationsRequest(apply=True),
        )

        self.assertEqual(applied.status, 'applied')
        self.assertEqual(
            list(self.task.codifier_content_entries.all()),
            [self.entry],
        )
        self.assertEqual(repeated.plan.content_count, 0)

    def test_command_defaults_to_preview_and_requires_apply_for_write(self):
        preview_output = StringIO()

        call_command(
            'backfill_task_classifications',
            stdout=preview_output,
        )

        self.assertFalse(self.task.codifier_content_entries.exists())
        self.assertIn('Dry-run', preview_output.getvalue())

        apply_output = StringIO()
        call_command(
            'backfill_task_classifications',
            '--apply',
            stdout=apply_output,
        )

        self.assertTrue(self.task.codifier_content_entries.exists())
        self.assertIn('связи применены', apply_output.getvalue())

    def test_container_wires_backfill_repository(self):
        use_case = Container().backfill_task_classifications_use_case()

        self.assertIsInstance(
            use_case.backfill_repo,
            DjangoTaskClassificationBackfillRepository,
        )
