from unittest import TestCase

from core_logic.entities.report import HeatmapStudentDetailData
from core_logic.use_cases.get_heatmap_student_detail import (
    GetHeatmapStudentDetailUseCase,
    HeatmapStudentDetailRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.topic_id = None
        self.student_id = None
        self.subtopic_id = None

    def get_heatmap_student_detail(self, topic_id, student_id, subtopic_id):
        self.topic_id = topic_id
        self.student_id = student_id
        self.subtopic_id = subtopic_id
        return HeatmapStudentDetailData(
            topic='topic',
            student='student',
            selected_subtopic='subtopic',
            details=[{'task': 'task'}],
            subtopic_summary=[{'subtopic': 'subtopic'}],
            courses=['course'],
        )


class GetHeatmapStudentDetailUseCaseTests(TestCase):
    def test_execute_returns_repository_detail_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapStudentDetailUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapStudentDetailRequest(
                topic_id='topic-1',
                student_id='student-1',
                subtopic_id='subtopic-1',
            ),
        )

        self.assertEqual(repo.topic_id, 'topic-1')
        self.assertEqual(repo.student_id, 'student-1')
        self.assertEqual(repo.subtopic_id, 'subtopic-1')
        self.assertEqual(data.details, [{'task': 'task'}])
        self.assertEqual(data.active_report, 'heatmap')
