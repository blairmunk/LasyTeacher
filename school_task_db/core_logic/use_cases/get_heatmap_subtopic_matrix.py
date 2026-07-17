"""Build student-subtopic heatmap matrix data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import HeatmapSubtopicMatrixData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapSubtopicMatrixRequest:
    student_ids: List[Any]
    topic_id: Any


class GetHeatmapSubtopicMatrixUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapSubtopicMatrixRequest,
    ) -> HeatmapSubtopicMatrixData:
        return self.report_repo.get_heatmap_subtopic_matrix(
            student_ids=request.student_ids,
            topic_id=request.topic_id,
        )
