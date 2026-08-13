from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapOverviewData,
    HeatmapTopicMatrixData,
)
from core_logic.entities.report_refs import ReportStudentRef
from core_logic.use_cases.get_heatmap_report import (
    GetHeatmapReportUseCase,
    HeatmapReportRequest,
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


class GetHeatmapReportUseCaseTests(TestCase):
    def test_builds_matrix_for_students_selected_by_overview(self):
        overview = self._overview((
            ReportStudentRef('student-1', 'Иванов Иван'),
        ))
        matrix = HeatmapTopicMatrixData((), (), ())
        overview_use_case = RecordingUseCase(overview)
        matrix_use_case = RecordingUseCase(matrix)

        result = GetHeatmapReportUseCase(
            overview_use_case,
            matrix_use_case,
        ).execute(HeatmapReportRequest('group-1', 'Механика'))

        self.assertIs(result.overview, overview)
        self.assertIs(result.matrix, matrix)
        self.assertEqual(result.section_filter, 'Механика')
        self.assertEqual(overview_use_case.requests[0].group_id, 'group-1')
        self.assertEqual(
            matrix_use_case.requests[0].student_ids,
            ('student-1',),
        )
        self.assertEqual(
            matrix_use_case.requests[0].section_filter,
            'Механика',
        )

    def test_skips_matrix_query_for_empty_overview(self):
        result = GetHeatmapReportUseCase(
            RecordingUseCase(self._overview()),
            FailingUseCase(),
        ).execute(HeatmapReportRequest())

        self.assertEqual(result.matrix.columns, ())

    @staticmethod
    def _overview(students=()):
        return HeatmapOverviewData(
            groups=(),
            selected_group=None,
            students=students,
            sections=(),
            courses=(),
        )
