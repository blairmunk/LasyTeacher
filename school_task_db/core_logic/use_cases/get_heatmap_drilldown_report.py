"""Build the complete topic drilldown heatmap scenario."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.heatmap import (
    HeatmapDrilldownReportData,
    HeatmapSubtopicMatrixData,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    GetHeatmapDrilldownOverviewUseCase,
    HeatmapDrilldownOverviewRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    GetHeatmapSubtopicMatrixUseCase,
    HeatmapSubtopicMatrixRequest,
)


@dataclass(frozen=True)
class HeatmapDrilldownReportRequest:
    topic_id: str
    group_id: Optional[str] = None


class GetHeatmapDrilldownReportUseCase:
    def __init__(
        self,
        overview_use_case: GetHeatmapDrilldownOverviewUseCase,
        matrix_use_case: GetHeatmapSubtopicMatrixUseCase,
    ):
        self.overview_use_case = overview_use_case
        self.matrix_use_case = matrix_use_case

    def execute(
        self,
        request: HeatmapDrilldownReportRequest,
    ) -> HeatmapDrilldownReportData:
        overview = self.overview_use_case.execute(
            HeatmapDrilldownOverviewRequest(
                topic_id=request.topic_id,
                group_id=request.group_id,
            ),
        )
        if not overview.students:
            matrix = HeatmapSubtopicMatrixData((), (), ())
        else:
            matrix = self.matrix_use_case.execute(
                HeatmapSubtopicMatrixRequest(
                    student_ids=tuple(
                        student.pk for student in overview.students
                    ),
                    topic_id=request.topic_id,
                ),
            )
        return HeatmapDrilldownReportData(
            overview=overview,
            matrix=matrix,
        )
