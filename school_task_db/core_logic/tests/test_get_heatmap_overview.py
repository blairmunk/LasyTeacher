from unittest import TestCase

from core_logic.entities.heatmap import HeatmapOverviewData
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
)
from core_logic.use_cases.get_heatmap_overview import (
    GetHeatmapOverviewUseCase,
    HeatmapOverviewRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.group_id = None

    def get_heatmap_overview(self, group_id):
        self.group_id = group_id
        group = ReportGroupRef(pk='group-1', name='7А')
        return HeatmapOverviewData(
            groups=(group,),
            selected_group=group,
            students=(ReportStudentRef(
                pk='student-1',
                full_name='Иванов Иван',
            ),),
            sections=('Механика',),
            courses=(ReportCourseRef(pk='course-1', name='Физика 7'),),
        )


class GetHeatmapOverviewUseCaseTests(TestCase):
    def test_execute_returns_repository_heatmap_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapOverviewUseCase(report_repo=repo)

        data = use_case.execute(HeatmapOverviewRequest(group_id='group-1'))

        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.groups[0].pk, 'group-1')
        self.assertEqual(data.students[0].pk, 'student-1')
        self.assertEqual(data.active_report, 'heatmap')
