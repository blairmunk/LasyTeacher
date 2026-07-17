from unittest import TestCase

from core_logic.entities.report import HeatmapSubtopicDetailData
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    GetHeatmapSubtopicDetailUseCase,
    HeatmapSubtopicDetailRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.subtopic_id = None
        self.group_id = None

    def get_heatmap_subtopic_detail(self, subtopic_id, group_id):
        self.subtopic_id = subtopic_id
        self.group_id = group_id
        return HeatmapSubtopicDetailData(
            subtopic='subtopic',
            topic='topic',
            groups=['group'],
            selected_group='group',
            student_rows=[{'student': 'student'}],
            task_rows=[{'task': 'task'}],
            overall_pct=80,
            overall_css='good',
            total_students=1,
            students_with_data=1,
            courses=['course'],
        )


class GetHeatmapSubtopicDetailUseCaseTests(TestCase):
    def test_execute_returns_repository_detail_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapSubtopicDetailUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapSubtopicDetailRequest(
                subtopic_id='subtopic-1',
                group_id='group-1',
            ),
        )

        self.assertEqual(repo.subtopic_id, 'subtopic-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.student_rows, [{'student': 'student'}])
        self.assertEqual(data.task_rows, [{'task': 'task'}])
        self.assertEqual(data.active_report, 'heatmap')
