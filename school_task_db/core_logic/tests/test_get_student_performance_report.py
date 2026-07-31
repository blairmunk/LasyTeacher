from unittest import TestCase

from datetime import datetime

from core_logic.entities.report import (
    ReportCourseRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    StudentPerformanceItemSource,
    StudentPerformanceParticipationFact,
    StudentPerformanceSource,
)
from core_logic.use_cases.get_student_performance_report import (
    GetStudentPerformanceReportUseCase,
    StudentPerformanceReportRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None
        self.group_id = None

    def get_student_performance_source(self, year, group_id):
        self.year = year
        self.group_id = group_id
        group = ReportGroupRef(pk='group-1', name='7А')
        return StudentPerformanceSource(
            students=[
                StudentPerformanceItemSource(
                    student=ReportStudentRef(
                        pk='student-1',
                        full_name='Иванов Иван',
                    ),
                    participations=[
                        StudentPerformanceParticipationFact(
                            status='graded',
                            created_at=datetime(2026, 9, 10),
                        ),
                    ],
                    marks=[
                        ReportMarkFact(
                            score=5,
                            points=9,
                            max_points=10,
                        ),
                    ],
                ),
            ],
            groups=[group],
            selected_group=group,
            courses=[ReportCourseRef(pk='course-1', name='Физика 7')],
        )


class GetStudentPerformanceReportUseCaseTests(TestCase):
    def test_execute_returns_repository_report_data(self):
        repo = FakeReportRepository()
        use_case = GetStudentPerformanceReportUseCase(report_repo=repo)

        data = use_case.execute(
            StudentPerformanceReportRequest(
                year='2026',
                group_id='group-1',
            ),
        )

        self.assertEqual(repo.year, '2026')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.students_stats[0]['student'].pk, 'student-1')
        self.assertEqual(data.students_stats[0]['average_pct'], 90)
        self.assertEqual(data.summary_stats['total_students'], 1)
        self.assertEqual(data.summary_stats['high_performers'], 1)
