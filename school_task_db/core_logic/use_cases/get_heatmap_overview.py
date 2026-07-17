"""Build base heatmap page data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import HeatmapOverviewData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapOverviewRequest:
    group_id: Any = None


class GetHeatmapOverviewUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(self, request: HeatmapOverviewRequest) -> HeatmapOverviewData:
        return self.report_repo.get_heatmap_overview(
            group_id=request.group_id,
        )
