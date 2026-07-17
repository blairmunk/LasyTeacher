from unittest import TestCase

from core_logic.use_cases.get_import_views import (
    GetImportHistoryUseCase,
    GetImportPageUseCase,
    ImportPageRequest,
)


class FakeCoreRepository:
    def __init__(self):
        self.recent_limit = None
        self.recent_logs = ['recent-a', 'recent-b']
        self.import_logs = ['log-a', 'log-b', 'log-c']

    def get_recent_import_logs(self, limit):
        self.recent_limit = limit
        return self.recent_logs

    def get_import_logs(self):
        return self.import_logs


class GetImportViewsUseCaseTests(TestCase):
    def test_get_import_page_returns_recent_logs_with_requested_limit(self):
        repo = FakeCoreRepository()
        use_case = GetImportPageUseCase(core_repo=repo)

        data = use_case.execute(ImportPageRequest(recent_limit=3))

        self.assertEqual(repo.recent_limit, 3)
        self.assertEqual(data.recent_imports, ['recent-a', 'recent-b'])

    def test_get_import_history_returns_all_logs(self):
        repo = FakeCoreRepository()
        use_case = GetImportHistoryUseCase(core_repo=repo)

        data = use_case.execute()

        self.assertEqual(data.imports, ['log-a', 'log-b', 'log-c'])
