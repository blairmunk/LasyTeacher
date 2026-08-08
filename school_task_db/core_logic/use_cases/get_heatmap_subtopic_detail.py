"""Build detailed subtopic heatmap data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.heatmap import HeatmapSubtopicDetailData
from core_logic.interfaces.heatmap_repo import IHeatmapRepository
from core_logic.services.heatmap_detail_service import HeatmapDetailService


@dataclass(frozen=True)
class HeatmapSubtopicDetailRequest:
    subtopic_id: Any
    group_id: Any = None


class GetHeatmapSubtopicDetailUseCase:
    def __init__(
        self,
        report_repo: IHeatmapRepository,
        detail_service: HeatmapDetailService | None = None,
    ):
        self.report_repo = report_repo
        self.detail_service = detail_service or HeatmapDetailService()

    def execute(
        self,
        request: HeatmapSubtopicDetailRequest,
    ) -> HeatmapSubtopicDetailData:
        source = self.report_repo.get_heatmap_subtopic_detail_source(
            subtopic_id=request.subtopic_id,
            group_id=request.group_id,
        )
        return self.detail_service.build_subtopic_detail(source)
