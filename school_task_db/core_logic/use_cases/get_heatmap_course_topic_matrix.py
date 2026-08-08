"""Build course student-topic heatmap matrix data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.heatmap import HeatmapTopicMatrixData
from core_logic.interfaces.heatmap_matrix_repo import IHeatmapMatrixRepository
from core_logic.services.heatmap_matrix_service import HeatmapMatrixService


@dataclass(frozen=True)
class HeatmapCourseTopicMatrixRequest:
    student_ids: List[Any]
    work_ids: List[Any]


class GetHeatmapCourseTopicMatrixUseCase:
    def __init__(
        self,
        report_repo: IHeatmapMatrixRepository,
        matrix_service: HeatmapMatrixService | None = None,
    ):
        self.report_repo = report_repo
        self.matrix_service = matrix_service or HeatmapMatrixService()

    def execute(
        self,
        request: HeatmapCourseTopicMatrixRequest,
    ) -> HeatmapTopicMatrixData:
        source = self.report_repo.get_heatmap_course_topic_matrix_source(
            student_ids=request.student_ids,
            work_ids=request.work_ids,
        )
        return self.matrix_service.build_topic_matrix(source)
