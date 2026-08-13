"""Build base course heatmap page data."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.heatmap import HeatmapCourseOverviewData
from core_logic.interfaces.heatmap_overview_repo import IHeatmapOverviewRepository


@dataclass(frozen=True)
class HeatmapCourseOverviewRequest:
    course_id: str
    group_id: Optional[str] = None


class GetHeatmapCourseOverviewUseCase:
    def __init__(self, report_repo: IHeatmapOverviewRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapCourseOverviewRequest,
    ) -> HeatmapCourseOverviewData:
        return self.report_repo.get_heatmap_course_overview(
            course_id=request.course_id,
            group_id=request.group_id,
        )
