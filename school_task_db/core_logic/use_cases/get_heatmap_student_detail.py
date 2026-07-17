"""Build detailed student heatmap data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import HeatmapStudentDetailData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapStudentDetailRequest:
    topic_id: Any
    student_id: Any
    subtopic_id: Any = None


class GetHeatmapStudentDetailUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapStudentDetailRequest,
    ) -> HeatmapStudentDetailData:
        return self.report_repo.get_heatmap_student_detail(
            topic_id=request.topic_id,
            student_id=request.student_id,
            subtopic_id=request.subtopic_id,
        )
