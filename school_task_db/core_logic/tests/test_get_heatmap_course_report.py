from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapColumnAverage,
    HeatmapCourseOverviewData,
    HeatmapCourseTimelineData,
    HeatmapMatrixCell,
    HeatmapMatrixRow,
    HeatmapTopicMatrixData,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportStudentRef,
    ReportWorkRef,
)
from core_logic.use_cases.get_heatmap_course_report import (
    GetHeatmapCourseReportUseCase,
    HeatmapCourseReportRequest,
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
        raise AssertionError('Dependent report query must not run')


class GetHeatmapCourseReportUseCaseTests(TestCase):
    def test_builds_complete_course_report_from_overview_scope(self):
        student = ReportStudentRef('student-1', 'Иванов Иван')
        work = ReportWorkRef(
            pk='work-1',
            name='Контрольная',
            work_type='control',
            work_type_display='Контрольная работа',
            duration=45,
        )
        overview = self._overview(students=(student,), works=(work,))
        column = ReportHeatmapColumnRef('topic-1', 'Кинематика')
        matrix = HeatmapTopicMatrixData(
            columns=(column,),
            rows=(HeatmapMatrixRow(
                student=student,
                cells=(HeatmapMatrixCell(column, 80, 'good'),),
                avg=80,
                avg_css='good',
            ),),
            col_averages=(HeatmapColumnAverage(80, 'good'),),
        )
        timeline = HeatmapCourseTimelineData(
            dates=('2026-08-01',),
            averages=(80,),
            labels=('Контрольная',),
        )
        overview_use_case = RecordingUseCase(overview)
        matrix_use_case = RecordingUseCase(matrix)
        timeline_use_case = RecordingUseCase(timeline)

        result = GetHeatmapCourseReportUseCase(
            overview_use_case,
            matrix_use_case,
            timeline_use_case,
        ).execute(HeatmapCourseReportRequest('course-1', 'group-1'))

        self.assertIs(result.overview, overview)
        self.assertIs(result.matrix, matrix)
        self.assertIs(result.timeline, timeline)
        self.assertEqual(
            overview_use_case.requests[0].course_id,
            'course-1',
        )
        self.assertEqual(overview_use_case.requests[0].group_id, 'group-1')
        self.assertEqual(
            matrix_use_case.requests[0].student_ids,
            ('student-1',),
        )
        self.assertEqual(matrix_use_case.requests[0].work_ids, ('work-1',))
        self.assertEqual(
            timeline_use_case.requests[0].student_ids,
            ('student-1',),
        )
        self.assertEqual(timeline_use_case.requests[0].work_ids, ('work-1',))

    def test_skips_matrix_queries_when_overview_has_no_students(self):
        overview = self._overview()

        result = GetHeatmapCourseReportUseCase(
            RecordingUseCase(overview),
            FailingUseCase(),
            FailingUseCase(),
        ).execute(HeatmapCourseReportRequest('course-1'))

        self.assertEqual(result.matrix.columns, ())
        self.assertEqual(result.matrix.rows, ())
        self.assertEqual(result.timeline.dates, ())

    @staticmethod
    def _overview(students=(), works=()):
        course = ReportCourseRef('course-1', 'Физика 7')
        return HeatmapCourseOverviewData(
            course=course,
            groups=(),
            selected_group=None,
            students=students,
            course_works=works,
            courses=(course,),
            active_course_pk=course.pk,
        )
