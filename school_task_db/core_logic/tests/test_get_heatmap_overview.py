from unittest import TestCase

from core_logic.entities.report import HeatmapOverviewData
from core_logic.use_cases.get_heatmap_overview import (
    GetHeatmapOverviewUseCase,
    HeatmapOverviewRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.group_id = None

    def get_heatmap_overview(self, group_id):
        self.group_id = group_id
        return HeatmapOverviewData(
            groups=['group'],
            selected_group='group',
            students=['student'],
            sections=['section'],
            courses=['course'],
        )


class GetHeatmapOverviewUseCaseTests(TestCase):
    def test_execute_returns_repository_heatmap_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapOverviewUseCase(report_repo=repo)

        data = use_case.execute(HeatmapOverviewRequest(group_id='group-1'))

        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.groups, ['group'])
        self.assertEqual(data.students, ['student'])
        self.assertEqual(data.active_report, 'heatmap')
