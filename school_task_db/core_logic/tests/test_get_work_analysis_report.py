from unittest import TestCase

from core_logic.entities.report import WorkAnalysisReportData
from core_logic.use_cases.get_work_analysis_report import (
    GetWorkAnalysisReportUseCase,
    WorkAnalysisReportRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None

    def get_work_analysis_report(self, year):
        self.year = year
        return WorkAnalysisReportData(
            works_analysis=[{'work': 'work'}],
            summary_stats={'total_works': 1},
            courses=['course'],
        )


class GetWorkAnalysisReportUseCaseTests(TestCase):
    def test_execute_returns_repository_report_data(self):
        repo = FakeReportRepository()
        use_case = GetWorkAnalysisReportUseCase(report_repo=repo)

        data = use_case.execute(WorkAnalysisReportRequest(year='2026'))

        self.assertEqual(repo.year, '2026')
        self.assertEqual(data.works_analysis, [{'work': 'work'}])
        self.assertEqual(data.summary_stats, {'total_works': 1})
