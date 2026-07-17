from unittest import TestCase

from core_logic.entities.report import JournalData
from core_logic.use_cases.get_journal import GetJournalUseCase, JournalRequest


class FakeReportRepository:
    def __init__(self):
        self.course_id = None
        self.group_id = None
        self.year = None
        self.show_debts_only = None

    def get_journal(self, course_id, group_id, year, show_debts_only):
        self.course_id = course_id
        self.group_id = group_id
        self.year = year
        self.show_debts_only = show_debts_only
        return JournalData(
            course='course',
            group='group',
            events=['event'],
            event_stats=[{'graded': 1}],
            rows=[{'student': 'student'}],
            all_rows_count=1,
            show_debts_only=show_debts_only,
            total_debts=0,
            students_with_debts=0,
            courses=['course'],
        )


class GetJournalUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeReportRepository()
        use_case = GetJournalUseCase(report_repo=repo)

        data = use_case.execute(
            JournalRequest(
                course_id='course-1',
                group_id='group-1',
                year='year',
                show_debts_only=True,
            ),
        )

        self.assertEqual(repo.course_id, 'course-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(repo.year, 'year')
        self.assertTrue(repo.show_debts_only)
        self.assertEqual(data.rows, [{'student': 'student'}])
        self.assertEqual(data.active_report, 'journal')
