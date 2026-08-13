"""Port for detailed heatmap source data."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.heatmap import (
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
)


class IHeatmapDetailRepository(ABC):
    @abstractmethod
    def get_heatmap_subtopic_detail_source(
        self,
        subtopic_id: str,
        group_id: Optional[str],
    ) -> HeatmapSubtopicDetailSource:
        """Return normalized facts for detailed subtopic analysis."""

    @abstractmethod
    def get_heatmap_student_detail_source(
        self,
        topic_id: str,
        student_id: str,
        subtopic_id: Optional[str],
    ) -> HeatmapStudentDetailSource:
        """Return normalized facts for one student's topic history."""
