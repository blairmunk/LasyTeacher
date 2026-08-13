from datetime import datetime
from unittest import TestCase

from core_logic.entities.report_summary import (
    EventsStatusSource,
    ReportStatusCount,
)
from core_logic.entities.report_refs import (
    ReportEventRef,
    ReportWorkRef,
)
from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
    GetEventsStatusReportUseCase,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None

    def get_events_status_source(self, year):
        self.year = year
        return EventsStatusSource(
            events=(
                ReportEventRef(
                    pk='event-1',
                    name='Событие',
                    status='planned',
                    status_display='Запланировано',
                    planned_date=datetime(2026, 7, 1, 12, 0),
                    work=ReportWorkRef(
                        pk='work-1',
                        name='Работа',
                        work_type='test',
                        work_type_display='Работа',
                        duration=45,
                    ),
                ),
            ),
            participation_statuses=('assigned',),
            courses=(),
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
        self.assertEqual(
            data.events_by_status,
            (ReportStatusCount(status='planned', count=1),),
        )
        self.assertEqual(
            data.participation_stats,
            (ReportStatusCount(status='assigned', count=1),),
        )
        self.assertEqual(data.all_events[0].pk, 'event-1')
        self.assertEqual(data.overdue_events[0].pk, 'event-1')
