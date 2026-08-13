"""Build base heatmap page data."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.heatmap import HeatmapOverviewData
from core_logic.interfaces.heatmap_overview_repo import IHeatmapOverviewRepository


@dataclass(frozen=True)
class HeatmapOverviewRequest:
    group_id: Optional[str] = None


class GetHeatmapOverviewUseCase:
    def __init__(self, report_repo: IHeatmapOverviewRepository):
        self.report_repo = report_repo

    def execute(self, request: HeatmapOverviewRequest) -> HeatmapOverviewData:
        return self.report_repo.get_heatmap_overview(
            group_id=request.group_id,
        )
