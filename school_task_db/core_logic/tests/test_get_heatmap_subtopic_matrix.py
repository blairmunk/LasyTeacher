from unittest import TestCase

from core_logic.entities.report import HeatmapSubtopicMatrixData
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    GetHeatmapSubtopicMatrixUseCase,
    HeatmapSubtopicMatrixRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.topic_id = None

    def get_heatmap_subtopic_matrix(self, student_ids, topic_id):
        self.student_ids = student_ids
        self.topic_id = topic_id
        return HeatmapSubtopicMatrixData(
            columns=['subtopic'],
            rows=[{'student': 'student'}],
            col_averages=[{'pct': 80}],
        )


class GetHeatmapSubtopicMatrixUseCaseTests(TestCase):
    def test_execute_returns_repository_matrix_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapSubtopicMatrixUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapSubtopicMatrixRequest(
                student_ids=['student-1'],
                topic_id='topic-1',
            ),
        )

        self.assertEqual(repo.student_ids, ['student-1'])
        self.assertEqual(repo.topic_id, 'topic-1')
        self.assertEqual(data.columns, ['subtopic'])
        self.assertEqual(data.col_averages, [{'pct': 80}])
