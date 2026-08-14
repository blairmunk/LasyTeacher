from unittest import TestCase

from core_logic.entities.core import GlobalSearchResults
from core_logic.use_cases.get_global_search import (
    GetGlobalSearchUseCase,
    GlobalSearchRequest,
)
from core_logic.value_objects.short_uuid import (
    format_short_uuid,
    uuid_matches_suffix,
)


class FakeCoreRepository:
    def __init__(self):
        self.uuid_query = None
        self.text_words = None
        self.uuid_results = GlobalSearchResults(tasks=('task',))
        self.text_results = GlobalSearchResults(tasks=('task-1', 'task-2'))

    def search_by_uuid(self, query):
        self.uuid_query = query
        return self.uuid_results

    def search_by_text(self, words):
        self.text_words = words
        return self.text_results


class GetGlobalSearchUseCaseTests(TestCase):
    def test_execute_returns_empty_data_for_blank_query(self):
        repo = FakeCoreRepository()
        use_case = GetGlobalSearchUseCase(core_repo=repo)

        data = use_case.execute(GlobalSearchRequest(raw_query='  '))

        self.assertEqual(data.query, '')
        self.assertEqual(data.results, GlobalSearchResults())
        self.assertEqual(data.total_found, 0)
        self.assertIsNone(data.search_mode)
        self.assertEqual(data.found_text, '')

    def test_execute_uses_uuid_search_for_hex_query(self):
        repo = FakeCoreRepository()
        use_case = GetGlobalSearchUseCase(core_repo=repo)

        data = use_case.execute(GlobalSearchRequest(raw_query='#ABC-123'))

        self.assertEqual(repo.uuid_query, 'abc123')
        self.assertIsNone(repo.text_words)
        self.assertEqual(data.search_mode, 'uuid')
        self.assertEqual(data.total_found, 1)
        self.assertEqual(data.found_text, '1 результат')

    def test_execute_falls_back_to_text_when_uuid_search_is_empty(self):
        repo = FakeCoreRepository()
        repo.uuid_results = GlobalSearchResults()
        use_case = GetGlobalSearchUseCase(core_repo=repo)

        data = use_case.execute(GlobalSearchRequest(raw_query='abc'))

        self.assertEqual(repo.uuid_query, 'abc')
        self.assertEqual(repo.text_words, ('abc',))
        self.assertEqual(data.search_mode, 'uuid+text')
        self.assertEqual(data.total_found, 2)

    def test_execute_uses_text_search_for_non_hex_query(self):
        repo = FakeCoreRepository()
        use_case = GetGlobalSearchUseCase(core_repo=repo)

        data = use_case.execute(GlobalSearchRequest(raw_query='  сила ток  '))

        self.assertIsNone(repo.uuid_query)
        self.assertEqual(repo.text_words, ('сила', 'ток'))
        self.assertEqual(data.search_mode, 'text')
        self.assertEqual(data.total_found, 2)
        self.assertEqual(data.found_text, '2 результата')

    def test_short_uuid_rule_matches_only_the_uuid_suffix(self):
        value = '550e8400-e29b-41d4-a716-44665544a7b3'

        self.assertEqual(format_short_uuid(value), 'A7B3')
        self.assertTrue(uuid_matches_suffix(value, '#A7-B3'))
        self.assertFalse(uuid_matches_suffix(value, '41d4'))
