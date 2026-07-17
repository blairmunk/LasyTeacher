from unittest import TestCase

from core_logic.entities.report import StudentPerformanceReportData
from core_logic.use_cases.get_student_performance_report import (
    GetStudentPerformanceReportUseCase,
    StudentPerformanceReportRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.year = None
        self.group_id = None

    def get_student_performance_report(self, year, group_id):
        self.year = year
        self.group_id = group_id
        return StudentPerformanceReportData(
            students_stats=[{'student': 'student'}],
            groups=['group'],
            selected_group='group',
            summary_stats={'total_students': 1},
            courses=['course'],
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
        self.assertEqual(data.students_stats, [{'student': 'student'}])
        self.assertEqual(data.summary_stats, {'total_students': 1})
