"""Build course heatmap timeline data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import HeatmapCourseTimelineData
from core_logic.interfaces.report_repo import IHeatmapRepository
from core_logic.services.heatmap_matrix_service import HeatmapMatrixService


@dataclass(frozen=True)
class HeatmapCourseTimelineRequest:
    student_ids: List[Any]
    work_ids: List[Any]


class GetHeatmapCourseTimelineUseCase:
    def __init__(
        self,
        report_repo: IHeatmapRepository,
        matrix_service: HeatmapMatrixService | None = None,
    ):
        self.report_repo = report_repo
        self.matrix_service = matrix_service or HeatmapMatrixService()

    def execute(
        self,
        request: HeatmapCourseTimelineRequest,
    ) -> HeatmapCourseTimelineData:
        source = self.report_repo.get_heatmap_course_timeline_source(
            student_ids=request.student_ids,
            work_ids=request.work_ids,
        )
        return self.matrix_service.build_course_timeline(source)
