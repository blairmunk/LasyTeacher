"""Build the complete student-topic heatmap scenario."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.heatmap import (
    HeatmapReportData,
    HeatmapTopicMatrixData,
)
from core_logic.use_cases.get_heatmap_overview import (
    GetHeatmapOverviewUseCase,
    HeatmapOverviewRequest,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    GetHeatmapTopicMatrixUseCase,
    HeatmapTopicMatrixRequest,
)


@dataclass(frozen=True)
class HeatmapReportRequest:
    group_id: Optional[str] = None
    section_filter: str = ''


class GetHeatmapReportUseCase:
    def __init__(
        self,
        overview_use_case: GetHeatmapOverviewUseCase,
        matrix_use_case: GetHeatmapTopicMatrixUseCase,
    ):
        self.overview_use_case = overview_use_case
        self.matrix_use_case = matrix_use_case

    def execute(self, request: HeatmapReportRequest) -> HeatmapReportData:
        overview = self.overview_use_case.execute(
            HeatmapOverviewRequest(group_id=request.group_id),
        )
        if not overview.students:
            matrix = HeatmapTopicMatrixData((), (), ())
        else:
            matrix = self.matrix_use_case.execute(
                HeatmapTopicMatrixRequest(
                    student_ids=tuple(
                        student.pk for student in overview.students
                    ),
                    section_filter=request.section_filter,
                ),
            )
        return HeatmapReportData(
            overview=overview,
            matrix=matrix,
            section_filter=request.section_filter,
        )
