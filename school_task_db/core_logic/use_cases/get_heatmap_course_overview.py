"""Build base course heatmap page data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import HeatmapCourseOverviewData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapCourseOverviewRequest:
    course_id: Any
    group_id: Any = None


class GetHeatmapCourseOverviewUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapCourseOverviewRequest,
    ) -> HeatmapCourseOverviewData:
        return self.report_repo.get_heatmap_course_overview(
            course_id=request.course_id,
            group_id=request.group_id,
        )
