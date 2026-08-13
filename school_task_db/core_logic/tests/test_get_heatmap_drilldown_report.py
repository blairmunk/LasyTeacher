from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapDrilldownOverviewData,
    HeatmapSubtopicMatrixData,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import ReportStudentRef
from core_logic.use_cases.get_heatmap_drilldown_report import (
    GetHeatmapDrilldownReportUseCase,
    HeatmapDrilldownReportRequest,
)


class RecordingUseCase:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.result


class FailingUseCase:
    def execute(self, request):
        raise AssertionError('Matrix query must not run')


class GetHeatmapDrilldownReportUseCaseTests(TestCase):
    def test_builds_subtopic_matrix_for_overview_students(self):
        overview = self._overview((
            ReportStudentRef('student-1', 'Иванов Иван'),
        ))
        matrix = HeatmapSubtopicMatrixData((), (), ())
        overview_use_case = RecordingUseCase(overview)
        matrix_use_case = RecordingUseCase(matrix)

        result = GetHeatmapDrilldownReportUseCase(
            overview_use_case,
            matrix_use_case,
        ).execute(HeatmapDrilldownReportRequest('topic-1', 'group-1'))

        self.assertIs(result.overview, overview)
        self.assertIs(result.matrix, matrix)
        self.assertEqual(overview_use_case.requests[0].topic_id, 'topic-1')
        self.assertEqual(overview_use_case.requests[0].group_id, 'group-1')
        self.assertEqual(
            matrix_use_case.requests[0].student_ids,
            ('student-1',),
        )
        self.assertEqual(matrix_use_case.requests[0].topic_id, 'topic-1')

    def test_skips_matrix_query_for_empty_overview(self):
        result = GetHeatmapDrilldownReportUseCase(
            RecordingUseCase(self._overview()),
            FailingUseCase(),
        ).execute(HeatmapDrilldownReportRequest('topic-1'))

        self.assertEqual(result.matrix.columns, ())

    @staticmethod
    def _overview(students=()):
        return HeatmapDrilldownOverviewData(
            topic=ReportHeatmapColumnRef('topic-1', 'Кинематика'),
            groups=(),
            selected_group=None,
            students=students,
            courses=(),
        )
