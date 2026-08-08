"""Build student-topic heatmap matrix data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.heatmap import HeatmapTopicMatrixData
from core_logic.interfaces.heatmap_repo import IHeatmapRepository
from core_logic.services.heatmap_matrix_service import HeatmapMatrixService


@dataclass(frozen=True)
class HeatmapTopicMatrixRequest:
    student_ids: List[Any]
    section_filter: str = ''


class GetHeatmapTopicMatrixUseCase:
    def __init__(
        self,
        report_repo: IHeatmapRepository,
        matrix_service: HeatmapMatrixService | None = None,
    ):
        self.report_repo = report_repo
        self.matrix_service = matrix_service or HeatmapMatrixService()

    def execute(
        self,
        request: HeatmapTopicMatrixRequest,
    ) -> HeatmapTopicMatrixData:
        source = self.report_repo.get_heatmap_topic_matrix_source(
            student_ids=request.student_ids,
            section_filter=request.section_filter,
        )
        return self.matrix_service.build_topic_matrix(source)
