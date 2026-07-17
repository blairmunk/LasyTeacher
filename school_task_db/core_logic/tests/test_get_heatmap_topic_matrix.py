from unittest import TestCase

from core_logic.entities.report import HeatmapTopicMatrixData
from core_logic.use_cases.get_heatmap_topic_matrix import (
    GetHeatmapTopicMatrixUseCase,
    HeatmapTopicMatrixRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.section_filter = None

    def get_heatmap_topic_matrix(self, student_ids, section_filter):
        self.student_ids = student_ids
        self.section_filter = section_filter
        return HeatmapTopicMatrixData(
            columns=['topic'],
            rows=[{'student': 'student'}],
            col_averages=[{'pct': 80}],
        )


class GetHeatmapTopicMatrixUseCaseTests(TestCase):
    def test_execute_returns_repository_matrix_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapTopicMatrixUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapTopicMatrixRequest(
                student_ids=['student-1'],
                section_filter='Кинематика',
            ),
        )

        self.assertEqual(repo.student_ids, ['student-1'])
        self.assertEqual(repo.section_filter, 'Кинематика')
        self.assertEqual(data.columns, ['topic'])
        self.assertEqual(data.col_averages, [{'pct': 80}])
