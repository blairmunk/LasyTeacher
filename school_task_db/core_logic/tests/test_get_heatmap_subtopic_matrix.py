from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapMatrixSource,
    HeatmapScoreFact,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import (
    ReportStudentRef,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    GetHeatmapSubtopicMatrixUseCase,
    HeatmapSubtopicMatrixRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.topic_id = None

    def get_heatmap_subtopic_matrix_source(self, student_ids, topic_id):
        self.student_ids = student_ids
        self.topic_id = topic_id
        return HeatmapMatrixSource(
            students=[
                ReportStudentRef(
                    pk='student-1',
                    full_name='Иванов Иван',
                ),
            ],
            columns=[
                ReportHeatmapColumnRef(
                    pk='subtopic-1',
                    name='Средняя скорость',
                ),
            ],
            scores=[
                HeatmapScoreFact(
                    student_id='student-1',
                    column_id='subtopic-1',
                    points=8,
                    max_points=10,
                ),
            ],
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
        self.assertEqual(data.columns[0].pk, 'subtopic-1')
        self.assertEqual(data.rows[0]['cells'][0]['subtopic'].pk, 'subtopic-1')
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])
