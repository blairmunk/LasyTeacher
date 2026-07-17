from unittest import TestCase

from core_logic.entities.report import HeatmapCourseOverviewData
from core_logic.use_cases.get_heatmap_course_overview import (
    GetHeatmapCourseOverviewUseCase,
    HeatmapCourseOverviewRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.course_id = None
        self.group_id = None

    def get_heatmap_course_overview(self, course_id, group_id):
        self.course_id = course_id
        self.group_id = group_id
        return HeatmapCourseOverviewData(
            course='course',
            groups=['group'],
            selected_group='group',
            students=['student'],
            course_works=['work'],
            courses=['course'],
            active_course_pk='course-1',
        )


class GetHeatmapCourseOverviewUseCaseTests(TestCase):
    def test_execute_returns_repository_course_heatmap_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapCourseOverviewUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapCourseOverviewRequest(
                course_id='course-1',
                group_id='group-1',
            ),
        )

        self.assertEqual(repo.course_id, 'course-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.course, 'course')
        self.assertEqual(data.course_works, ['work'])
        self.assertEqual(data.active_report, 'heatmap-course')
