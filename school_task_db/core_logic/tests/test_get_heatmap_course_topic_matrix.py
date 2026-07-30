from unittest import TestCase

from core_logic.entities.report import (
    HeatmapMatrixSource,
    HeatmapScoreFact,
    ReportHeatmapColumnRef,
    ReportStudentRef,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
    HeatmapCourseTopicMatrixRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.work_ids = None

    def get_heatmap_course_topic_matrix_source(self, student_ids, work_ids):
        self.student_ids = student_ids
        self.work_ids = work_ids
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
        self.assertEqual(data.columns[0].pk, 'topic-1')
        self.assertEqual(data.rows[0]['avg'], 80)
        self.assertEqual(data.col_averages, [{'pct': 80, 'css': 'good'}])
