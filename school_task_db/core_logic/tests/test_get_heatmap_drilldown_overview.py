from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapDrilldownOverviewData,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    GetHeatmapDrilldownOverviewUseCase,
    HeatmapDrilldownOverviewRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.topic_id = None
        self.group_id = None

    def get_heatmap_drilldown_overview(self, topic_id, group_id):
        self.topic_id = topic_id
        self.group_id = group_id
        group = ReportGroupRef(pk='group-1', name='7А')
        return HeatmapDrilldownOverviewData(
            topic=ReportHeatmapColumnRef(pk='topic-1', name='Механика'),
            groups=(group,),
            selected_group=group,
            students=(ReportStudentRef(
                pk='student-1',
                full_name='Иванов Иван',
            ),),
            courses=(ReportCourseRef(pk='course-1', name='Физика 7'),),
        )


class GetHeatmapDrilldownOverviewUseCaseTests(TestCase):
    def test_execute_returns_repository_drilldown_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapDrilldownOverviewUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapDrilldownOverviewRequest(
                topic_id='topic-1',
                group_id='group-1',
            ),
        )

        self.assertEqual(repo.topic_id, 'topic-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.topic.pk, 'topic-1')
        self.assertEqual(data.active_report, 'heatmap')
