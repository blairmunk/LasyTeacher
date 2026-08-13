from unittest import TestCase

from core_logic.entities.journal import JournalSelectData, JournalSelectLink
from core_logic.entities.report_refs import ReportCourseRef, ReportGroupRef
from core_logic.use_cases.get_journal_select import (
    GetJournalSelectUseCase,
    JournalSelectRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None

    def get_journal_select(self, year):
        self.year = year
        course = ReportCourseRef(pk='course-1', name='Физика')
        group = ReportGroupRef(pk='group-1', name='7А')
        return JournalSelectData(
            journal_links=(JournalSelectLink(
                course=course,
                group=group,
                event_count=2,
            ),),
            groups=(group,),
            courses=(course,),
        )


class GetJournalSelectUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeReportRepository()
        use_case = GetJournalSelectUseCase(report_repo=repo)

        data = use_case.execute(JournalSelectRequest(year='year'))

        self.assertEqual(repo.year, 'year')
        self.assertEqual(data.journal_links[0].course.pk, 'course-1')
        self.assertEqual(data.journal_links[0].group.pk, 'group-1')
        self.assertEqual(data.journal_links[0].event_count, 2)
        self.assertEqual(data.active_report, 'journal')
