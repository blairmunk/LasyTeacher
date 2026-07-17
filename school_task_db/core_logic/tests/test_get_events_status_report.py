from datetime import datetime
from unittest import TestCase

from core_logic.entities.report import EventsStatusReportData
from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
    GetEventsStatusReportUseCase,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None
        self.current_date = None

    def get_events_status_report(self, year, current_date):
        self.year = year
        self.current_date = current_date
        return EventsStatusReportData(
            events_by_status=[{'status': 'planned', 'count': 1}],
            overdue_events=['overdue'],
            long_reviewing=[],
            completed_unchecked=[],
            participation_stats=[],
            all_events=['event'],
            courses=['course'],
        )


class GetEventsStatusReportUseCaseTests(TestCase):
    def test_execute_returns_repository_report_data(self):
        repo = FakeReportRepository()
        current_date = datetime(2026, 7, 17, 12, 0)
        use_case = GetEventsStatusReportUseCase(report_repo=repo)

        data = use_case.execute(
            EventsStatusReportRequest(
                year='2026',
                current_date=current_date,
            ),
        )

        self.assertEqual(repo.year, '2026')
        self.assertEqual(repo.current_date, current_date)
        self.assertEqual(data.events_by_status, [{'status': 'planned', 'count': 1}])
        self.assertEqual(data.all_events, ['event'])
