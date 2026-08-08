"""Port for detailed heatmap source data."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.heatmap import (
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
)


class IHeatmapDetailRepository(ABC):
    @abstractmethod
    def get_heatmap_subtopic_detail_source(
        self,
        subtopic_id: Any,
        group_id: Any,
    ) -> HeatmapSubtopicDetailSource:
        """Return normalized facts for detailed subtopic analysis."""

    @abstractmethod
    def get_heatmap_student_detail_source(
        self,
        topic_id: Any,
        student_id: Any,
        subtopic_id: Any,
    ) -> HeatmapStudentDetailSource:
        """Return normalized facts for one student's topic history."""
