"""Port for heatmap overview data."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.heatmap import (
    HeatmapCourseOverviewData,
    HeatmapDrilldownOverviewData,
    HeatmapOverviewData,
)


class IHeatmapOverviewRepository(ABC):
    @abstractmethod
    def get_heatmap_overview(
        self,
        group_id: Optional[str],
    ) -> HeatmapOverviewData:
        """Return base heatmap data."""

    @abstractmethod
    def get_heatmap_course_overview(
        self,
        course_id: str,
        group_id: Optional[str],
    ) -> HeatmapCourseOverviewData:
        """Return base course heatmap data."""

    @abstractmethod
    def get_heatmap_drilldown_overview(
        self,
        topic_id: str,
        group_id: Optional[str],
    ) -> HeatmapDrilldownOverviewData:
        """Return base topic drilldown heatmap data."""
