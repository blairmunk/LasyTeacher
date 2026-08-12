from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from core_logic.entities.task_image_audit import TaskImagePositionSuggestion
from curriculum.models import Topic
from infrastructure.repositories.django_task_image_audit_command_repo import (
    DjangoTaskImageAuditCommandRepository,
)
from infrastructure.repositories.django_task_image_audit_query_repo import (
    DjangoTaskImageAuditQueryRepository,
)
from tasks.models import Task, TaskImage


class DjangoTaskImageAuditRepositoryAdaptersTests(TestCase):
    def setUp(self):
        topic = Topic.objects.create(
            name='Оптика',
            subject='Физика',
            grade_level=8,
        )
        task = Task.objects.create(
            text='Постройте изображение в линзе',
            answer='Чертёж',
            topic=topic,
            difficulty=2,
            task_type='computational',
        )
        self.missing_image = TaskImage.objects.create(
            task=task,
            image='task_images/lens.png',
            caption='Схема установки',
            position='',
        )
        self.positioned_image = TaskImage.objects.create(
            task=task,
            image='task_images/table.png',
            caption='Таблица',
            position='right_40',
        )

    def test_lists_audit_sources_and_updates_only_missing_positions(self):
        query_repo = DjangoTaskImageAuditQueryRepository()
        command_repo = DjangoTaskImageAuditCommandRepository()

        sources = query_repo.list_task_images()
        updated = command_repo.apply_position_suggestions([
            TaskImagePositionSuggestion(
                image_id=str(self.missing_image.pk),
                position='bottom_70',
                position_label='Снизу по центру 70% ширины',
            ),
            TaskImagePositionSuggestion(
                image_id=str(self.positioned_image.pk),
                position='bottom_100',
                position_label='Снизу по центру 100% ширины',
            ),
        ])

        self.missing_image.refresh_from_db()
        self.positioned_image.refresh_from_db()
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].topic_name, 'Оптика')
        self.assertEqual(updated, 1)
        self.assertEqual(self.missing_image.position, 'bottom_70')
        self.assertEqual(self.positioned_image.position, 'right_40')

    @patch('builtins.input', return_value='y')
    def test_analyze_images_command_applies_confirmed_suggestions(self, _input):
        output = StringIO()

        call_command(
            'analyze_images',
            '--show-missing',
            '--fix-missing',
            stdout=output,
        )

        self.missing_image.refresh_from_db()
        self.assertEqual(self.missing_image.position, 'bottom_70')
        self.assertIn('ИЗОБРАЖЕНИЯ БЕЗ ПОЗИЦИИ: 1', output.getvalue())
        self.assertIn('Обновлено позиций: 1', output.getvalue())
