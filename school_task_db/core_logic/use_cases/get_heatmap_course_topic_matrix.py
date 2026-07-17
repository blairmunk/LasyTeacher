"""Build course student-topic heatmap matrix data."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import HeatmapTopicMatrixData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class HeatmapCourseTopicMatrixRequest:
    student_ids: List[Any]
    work_ids: List[Any]


class GetHeatmapCourseTopicMatrixUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: HeatmapCourseTopicMatrixRequest,
    ) -> HeatmapTopicMatrixData:
        return self.report_repo.get_heatmap_course_topic_matrix(
            student_ids=request.student_ids,
            work_ids=request.work_ids,
        )
