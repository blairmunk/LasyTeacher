"""Build detailed subtopic heatmap data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import HeatmapSubtopicDetailData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapSubtopicDetailRequest:
    subtopic_id: Any
    group_id: Any = None


class GetHeatmapSubtopicDetailUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapSubtopicDetailRequest,
    ) -> HeatmapSubtopicDetailData:
        return self.report_repo.get_heatmap_subtopic_detail(
            subtopic_id=request.subtopic_id,
            group_id=request.group_id,
        )
