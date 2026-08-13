from unittest import TestCase

from core_logic.entities.heatmap import HeatmapCourseOverviewData
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
    ReportWorkRef,
)
from core_logic.use_cases.get_heatmap_course_overview import (
    GetHeatmapCourseOverviewUseCase,
    HeatmapCourseOverviewRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.course_id = None
        self.group_id = None

    def get_heatmap_course_overview(self, course_id, group_id):
        self.course_id = course_id
        self.group_id = group_id
        course = ReportCourseRef(pk='course-1', name='Физика 7')
        group = ReportGroupRef(pk='group-1', name='7А')
        return HeatmapCourseOverviewData(
            course=course,
            groups=(group,),
            selected_group=group,
            students=(ReportStudentRef(
                pk='student-1',
                full_name='Иванов Иван',
            ),),
            course_works=(ReportWorkRef(
                pk='work-1',
                name='Контрольная',
                work_type='control',
                work_type_display='Контрольная работа',
                duration=45,
            ),),
            courses=(course,),
            active_course_pk='course-1',
        )


class GetHeatmapCourseOverviewUseCaseTests(TestCase):
    def test_execute_returns_repository_course_heatmap_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapCourseOverviewUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapCourseOverviewRequest(
                course_id='course-1',
                group_id='group-1',
            ),
        )

        self.assertEqual(repo.course_id, 'course-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.course.pk, 'course-1')
        self.assertEqual(data.course_works[0].pk, 'work-1')
        self.assertEqual(data.active_report, 'heatmap-course')
