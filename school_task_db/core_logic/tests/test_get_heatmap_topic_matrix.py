from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapMatrixSource,
    HeatmapScoreFact,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import (
    ReportStudentRef,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    GetHeatmapTopicMatrixUseCase,
    HeatmapTopicMatrixRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.section_filter = None

    def get_heatmap_topic_matrix_source(self, student_ids, section_filter):
        self.student_ids = student_ids
        self.section_filter = section_filter
        return HeatmapMatrixSource(
            students=[
                ReportStudentRef(
                    pk='student-1',
                    full_name='Иванов Иван',
                ),
            ],
            columns=[
                ReportHeatmapColumnRef(
                    pk='topic-1',
                    name='Кинематика',
                ),
            ],
            scores=[
                HeatmapScoreFact(
                    student_id='student-1',
                    column_id='topic-1',
                    points=8,
                    max_points=10,
                ),
            ],
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
        self.assertEqual(data.columns[0].pk, 'topic-1')
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])
