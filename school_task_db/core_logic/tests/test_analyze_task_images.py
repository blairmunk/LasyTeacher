from unittest import TestCase

from core_logic.entities.task_image_audit import TaskImageAuditSource
from core_logic.use_cases.analyze_task_images import (
    AnalyzeTaskImagesUseCase,
    ApplyTaskImagePositionSuggestionsUseCase,
)


class FakeTaskImageAuditRepository:
    def __init__(self, images=()):
        self.images = tuple(images)
        self.applied_suggestions = ()

    def list_task_images(self):
        return self.images

    def apply_position_suggestions(self, suggestions):
        self.applied_suggestions = tuple(suggestions)
        return len(self.applied_suggestions)


class AnalyzeTaskImagesUseCaseTests(TestCase):
    def test_builds_distribution_and_missing_position_suggestions(self):
        repo = FakeTaskImageAuditRepository([
            TaskImageAuditSource(
                pk='image-1',
                task_text='Задание 1',
                topic_name='Механика',
                filename='graph.png',
                caption='График движения',
                position='',
            ),
            TaskImageAuditSource(
                pk='image-2',
                task_text='Задание 2',
                topic_name='Механика',
                filename='portrait.png',
                caption='Фото учёного',
                position='',
            ),
            TaskImageAuditSource(
                pk='image-3',
                task_text='Задание 3',
                topic_name='Механика',
                filename='table.png',
                caption='Таблица измерений',
                position='right_40',
            ),
        ])

        result = AnalyzeTaskImagesUseCase(repo).execute()

        self.assertEqual(result.total_images, 3)
        self.assertEqual(result.missing_count, 2)
        self.assertEqual(
            {item.position: item.count for item in result.distribution},
            {'missing': 2, 'right_40': 1},
        )
        self.assertEqual(
            [suggestion.position for suggestion in result.suggestions],
            ['bottom_70', 'right_20'],
        )

    def test_apply_delegates_suggestions_to_repository(self):
        repo = FakeTaskImageAuditRepository()
        suggestions = AnalyzeTaskImagesUseCase(
            FakeTaskImageAuditRepository([
                TaskImageAuditSource(
                    pk='image-1',
                    task_text='Задание',
                    topic_name='Механика',
                    filename='table.png',
                    caption='Таблица',
                ),
            ]),
        ).execute().suggestions

        updated = ApplyTaskImagePositionSuggestionsUseCase(repo).execute(
            suggestions,
        )

        self.assertEqual(updated, 1)
        self.assertEqual(repo.applied_suggestions, suggestions)
        self.assertEqual(suggestions[0].position, 'bottom_100')
