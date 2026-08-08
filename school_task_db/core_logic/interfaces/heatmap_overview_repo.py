"""Port for heatmap overview data."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.heatmap import (
    HeatmapCourseOverviewData,
    HeatmapDrilldownOverviewData,
    HeatmapOverviewData,
)


class IHeatmapOverviewRepository(ABC):
    @abstractmethod
    def get_heatmap_overview(self, group_id: Any) -> HeatmapOverviewData:
        """Return base heatmap data."""

    @abstractmethod
    def get_heatmap_course_overview(
        self,
        course_id: Any,
        group_id: Any,
    ) -> HeatmapCourseOverviewData:
        """Return base course heatmap data."""

    @abstractmethod
    def get_heatmap_drilldown_overview(
        self,
        topic_id: Any,
        group_id: Any,
    ) -> HeatmapDrilldownOverviewData:
        """Return base topic drilldown heatmap data."""
