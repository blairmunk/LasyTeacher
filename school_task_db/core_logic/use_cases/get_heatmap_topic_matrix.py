"""Build student-topic heatmap matrix data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import HeatmapTopicMatrixData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapTopicMatrixRequest:
    student_ids: List[Any]
    section_filter: str = ''


class GetHeatmapTopicMatrixUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapTopicMatrixRequest,
    ) -> HeatmapTopicMatrixData:
        return self.report_repo.get_heatmap_topic_matrix(
            student_ids=request.student_ids,
            section_filter=request.section_filter,
        )
