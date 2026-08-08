from unittest import TestCase

from core_logic.entities.report_summary import (
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportMarkFact,
    ReportWorkRef,
)
from core_logic.use_cases.get_work_analysis_report import (
    GetWorkAnalysisReportUseCase,
    WorkAnalysisReportRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None

    def get_work_analysis_source(self, year):
        self.year = year
        return WorkAnalysisSource(
            works=[
                WorkAnalysisItemSource(
                    work=ReportWorkRef(
                        pk='work-1',
                        name='Контрольная',
                        work_type='control',
                        work_type_display='Контрольная работа',
                        duration=45,
                    ),
                    events_count=1,
                    marks=[
                        ReportMarkFact(score=4, points=8, max_points=10),
                    ],
                ),
            ],
            courses=[ReportCourseRef(pk='course-1', name='Физика 7')],
        )


class GetWorkAnalysisReportUseCaseTests(TestCase):
    def test_execute_returns_repository_report_data(self):
        repo = FakeReportRepository()
        use_case = GetWorkAnalysisReportUseCase(report_repo=repo)

        data = use_case.execute(WorkAnalysisReportRequest(year='2026'))

        self.assertEqual(repo.year, '2026')
        self.assertEqual(data.works_analysis[0]['work'].pk, 'work-1')
        self.assertEqual(data.works_analysis[0]['average_percentage'], 80)
        self.assertEqual(data.summary_stats['total_works'], 1)
