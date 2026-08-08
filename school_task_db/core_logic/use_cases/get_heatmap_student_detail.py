"""Build detailed student heatmap data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import HeatmapStudentDetailData
from core_logic.interfaces.report_repo import IHeatmapRepository
from core_logic.services.heatmap_detail_service import HeatmapDetailService


@dataclass(frozen=True)
class HeatmapStudentDetailRequest:
    topic_id: Any
    student_id: Any
    subtopic_id: Any = None


class GetHeatmapStudentDetailUseCase:
    def __init__(
        self,
        report_repo: IHeatmapRepository,
        detail_service: HeatmapDetailService | None = None,
    ):
        self.report_repo = report_repo
        self.detail_service = detail_service or HeatmapDetailService()

    def execute(
        self,
        request: HeatmapStudentDetailRequest,
    ) -> HeatmapStudentDetailData:
        source = self.report_repo.get_heatmap_student_detail_source(
            topic_id=request.topic_id,
            student_id=request.student_id,
            subtopic_id=request.subtopic_id,
        )
        return self.detail_service.build_student_detail(source)
