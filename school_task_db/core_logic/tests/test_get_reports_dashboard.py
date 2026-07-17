from datetime import datetime
from unittest import TestCase

from core_logic.entities.report import ReportsDashboardData
from core_logic.use_cases.get_reports_dashboard import (
    GetReportsDashboardUseCase,
    ReportsDashboardRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None
        self.current_date = None

    def get_reports_dashboard(self, year, current_date):
        self.year = year
        self.current_date = current_date
        return ReportsDashboardData(
            total_students=1,
            total_events=2,
            total_works=3,
            total_courses=4,
            total_marks=5,
            average_score=4.5,
            marks_last_month=1,
            score_counts={5: 1},
            events_planned=1,
            events_completed=0,
            events_graded=1,
            monthly_labels=['Jan 2026'],
            monthly_values=[1],
            class_stats=[{'name': '7А'}],
            class_names=['7А'],
            class_avg_scores=[4.5],
            class_completion=[100],
            recent_events=['event'],
            event_status_counts={'graded': 1},
            box_data={'work': [5]},
            courses=['course'],
        )


class GetReportsDashboardUseCaseTests(TestCase):
    def test_execute_returns_repository_report_data(self):
        repo = FakeReportRepository()
        use_case = GetReportsDashboardUseCase(report_repo=repo)
        current_date = datetime(2026, 1, 15)

        data = use_case.execute(
            ReportsDashboardRequest(
                year='2026',
                current_date=current_date,
            ),
        )

        self.assertEqual(repo.year, '2026')
        self.assertEqual(repo.current_date, current_date)
        self.assertEqual(data.total_students, 1)
        self.assertEqual(data.score_counts, {5: 1})
        self.assertEqual(data.active_report, 'dashboard')
