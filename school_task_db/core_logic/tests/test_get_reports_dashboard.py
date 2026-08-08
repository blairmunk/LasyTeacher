from datetime import datetime
from unittest import TestCase

from core_logic.entities.report_summary import (
    DashboardCourseGroupRef,
    DashboardGroupSource,
    DashboardMarkFact,
    DashboardParticipationFact,
    ReportsDashboardSource,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportWorkRef,
)
from core_logic.use_cases.get_reports_dashboard import (
    GetReportsDashboardUseCase,
    ReportsDashboardRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None

    def get_reports_dashboard_source(self, year):
        self.year = year
        course = ReportCourseRef(pk='course-1', name='Физика 7')
        return ReportsDashboardSource(
            total_students=1,
            total_works=3,
            events=[
                ReportEventRef(
                    pk='event-1',
                    name='КР',
                    status='graded',
                    status_display='Проверено',
                    planned_date=datetime(2026, 1, 10),
                    work=ReportWorkRef(
                        pk='work-1',
                        name='Контрольная',
                        work_type='test',
                        work_type_display='Контрольная работа',
                        duration=45,
                    ),
                ),
            ],
            participations=[
                DashboardParticipationFact(
                    student_id='student-1',
                    event_id='event-1',
                    status='graded',
                ),
            ],
            marks=[
                DashboardMarkFact(
                    student_id='student-1',
                    event_id='event-1',
                    score=5,
                    checked_at=datetime(2026, 1, 10),
                ),
            ],
            groups=[
                DashboardGroupSource(
                    group=ReportGroupRef(
                        pk='group-1',
                        name='7А',
                        students_count=1,
                    ),
                    student_ids=['student-1'],
                    course_links=[
                        DashboardCourseGroupRef(
                            course_id='course-1',
                            course_name='Физика 7',
                            group_id='group-1',
                            group_name='7А',
                        ),
                    ],
                ),
            ],
            courses=[course],
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
        self.assertEqual(data.total_students, 1)
        self.assertEqual(data.total_events, 1)
        self.assertEqual(data.total_courses, 1)
        self.assertEqual(data.score_counts, {5: 1})
        self.assertEqual(data.class_stats[0]['completion_rate'], 100)
        self.assertEqual(data.box_data, {'Контрольная': [5]})
        self.assertEqual(data.active_report, 'dashboard')
