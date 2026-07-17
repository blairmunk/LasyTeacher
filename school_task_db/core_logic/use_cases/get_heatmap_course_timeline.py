"""Build course heatmap timeline data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import HeatmapCourseTimelineData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapCourseTimelineRequest:
    student_ids: List[Any]
    work_ids: List[Any]


class GetHeatmapCourseTimelineUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapCourseTimelineRequest,
    ) -> HeatmapCourseTimelineData:
        return self.report_repo.get_heatmap_course_timeline(
            student_ids=request.student_ids,
            work_ids=request.work_ids,
        )
