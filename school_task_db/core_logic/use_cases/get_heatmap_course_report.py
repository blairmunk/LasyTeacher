"""Build the complete course heatmap reporting scenario."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.heatmap import (
    HeatmapCourseReportData,
    HeatmapCourseTimelineData,
    HeatmapTopicMatrixData,
)
from core_logic.use_cases.get_heatmap_course_overview import (
    GetHeatmapCourseOverviewUseCase,
    HeatmapCourseOverviewRequest,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    GetHeatmapCourseTimelineUseCase,
    HeatmapCourseTimelineRequest,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
    HeatmapCourseTopicMatrixRequest,
)


@dataclass(frozen=True)
class HeatmapCourseReportRequest:
    course_id: str
    group_id: Optional[str] = None


class GetHeatmapCourseReportUseCase:
    def __init__(
        self,
        overview_use_case: GetHeatmapCourseOverviewUseCase,
        matrix_use_case: GetHeatmapCourseTopicMatrixUseCase,
        timeline_use_case: GetHeatmapCourseTimelineUseCase,
    ):
        self.overview_use_case = overview_use_case
        self.matrix_use_case = matrix_use_case
        self.timeline_use_case = timeline_use_case

    def execute(
        self,
        request: HeatmapCourseReportRequest,
    ) -> HeatmapCourseReportData:
        overview = self.overview_use_case.execute(
            HeatmapCourseOverviewRequest(
                course_id=request.course_id,
                group_id=request.group_id,
            ),
        )
        if not overview.students:
            return HeatmapCourseReportData(
                overview=overview,
                matrix=HeatmapTopicMatrixData((), (), ()),
                timeline=HeatmapCourseTimelineData((), (), ()),
            )

        student_ids = tuple(student.pk for student in overview.students)
        work_ids = tuple(work.pk for work in overview.course_works)
        matrix = self.matrix_use_case.execute(
            HeatmapCourseTopicMatrixRequest(
                student_ids=student_ids,
                work_ids=work_ids,
            ),
        )
        timeline = self.timeline_use_case.execute(
            HeatmapCourseTimelineRequest(
                student_ids=student_ids,
                work_ids=work_ids,
            ),
        )
        return HeatmapCourseReportData(
            overview=overview,
            matrix=matrix,
            timeline=timeline,
        )
