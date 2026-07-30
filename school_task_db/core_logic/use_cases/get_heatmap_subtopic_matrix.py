"""Build student-subtopic heatmap matrix data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import HeatmapSubtopicMatrixData
from core_logic.interfaces.report_repo import IReportRepository
from core_logic.services.heatmap_matrix_service import HeatmapMatrixService


@dataclass(frozen=True)
class HeatmapSubtopicMatrixRequest:
    student_ids: List[Any]
    topic_id: Any


class GetHeatmapSubtopicMatrixUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        matrix_service: HeatmapMatrixService | None = None,
    ):
        self.report_repo = report_repo
        self.matrix_service = matrix_service or HeatmapMatrixService()

    def execute(
        self,
        request: HeatmapSubtopicMatrixRequest,
    ) -> HeatmapSubtopicMatrixData:
        source = self.report_repo.get_heatmap_subtopic_matrix_source(
            student_ids=request.student_ids,
            topic_id=request.topic_id,
        )
        return self.matrix_service.build_subtopic_matrix(source)
