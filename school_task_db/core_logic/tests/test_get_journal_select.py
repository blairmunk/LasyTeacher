from unittest import TestCase

from core_logic.entities.report import JournalSelectData
from core_logic.use_cases.get_journal_select import (
    GetJournalSelectUseCase,
    JournalSelectRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None

    def get_journal_select(self, year):
        self.year = year
        return JournalSelectData(
            journal_links=[{'course': 'course'}],
            groups=['group'],
            courses=['course'],
        )


class GetJournalSelectUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeReportRepository()
        use_case = GetJournalSelectUseCase(report_repo=repo)

        data = use_case.execute(JournalSelectRequest(year='year'))

        self.assertEqual(repo.year, 'year')
        self.assertEqual(data.journal_links, [{'course': 'course'}])
        self.assertEqual(data.active_report, 'journal')
