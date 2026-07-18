from unittest import TestCase

from core_logic.entities.task import SourceCreateParams, SourceCreateResult
from core_logic.use_cases.create_source import CreateSourceUseCase


class FakeTaskRepository:
    def __init__(self):
        self.created_params = None

    def create_source(self, params):
        self.created_params = params
        return SourceCreateResult(pk='source-1', display_name='Сборник')


class CreateSourceUseCaseTests(TestCase):
    def test_execute_delegates_to_repository(self):
        repo = FakeTaskRepository()
        use_case = CreateSourceUseCase(task_repo=repo)
        params = SourceCreateParams(
            name='Сборник задач',
            short_name='Сборник',
            source_type='problem_book',
            author='Автор',
            year=2026,
            url='https://example.test',
            isbn='123',
            notes='Заметки',
        )

        result = use_case.execute(params)

        self.assertEqual(result.pk, 'source-1')
        self.assertEqual(result.display_name, 'Сборник')
        self.assertEqual(repo.created_params, params)
