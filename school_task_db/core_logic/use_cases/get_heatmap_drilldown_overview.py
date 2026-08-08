"""Build base topic drilldown heatmap page data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.heatmap import HeatmapDrilldownOverviewData
from core_logic.interfaces.heatmap_overview_repo import IHeatmapOverviewRepository


@dataclass(frozen=True)
class HeatmapDrilldownOverviewRequest:
    topic_id: Any
    group_id: Any = None


class GetHeatmapDrilldownOverviewUseCase:
    def __init__(self, report_repo: IHeatmapOverviewRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapDrilldownOverviewRequest,
    ) -> HeatmapDrilldownOverviewData:
        return self.report_repo.get_heatmap_drilldown_overview(
            topic_id=request.topic_id,
            group_id=request.group_id,
        )
