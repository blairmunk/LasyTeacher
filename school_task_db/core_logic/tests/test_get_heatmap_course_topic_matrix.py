from unittest import TestCase

from core_logic.entities.report import HeatmapTopicMatrixData
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
    HeatmapCourseTopicMatrixRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.work_ids = None

    def get_heatmap_course_topic_matrix(self, student_ids, work_ids):
        self.student_ids = student_ids
        self.work_ids = work_ids
        return HeatmapTopicMatrixData(
            columns=['topic'],
            rows=[{'student': 'student'}],
            col_averages=[{'pct': 80}],
        )


class GetHeatmapCourseTopicMatrixUseCaseTests(TestCase):
    def test_execute_returns_repository_matrix_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapCourseTopicMatrixUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapCourseTopicMatrixRequest(
                student_ids=['student-1'],
                work_ids=['work-1'],
            ),
        )

        self.assertEqual(repo.student_ids, ['student-1'])
        self.assertEqual(repo.work_ids, ['work-1'])
        self.assertEqual(data.columns, ['topic'])
        self.assertEqual(data.col_averages, [{'pct': 80}])
