"""Port for heatmap matrix and timeline source data."""

from abc import ABC, abstractmethod
from core_logic.entities.heatmap import (
    HeatmapCourseTimelineSource,
    HeatmapMatrixSource,
)


class IHeatmapMatrixRepository(ABC):
    @abstractmethod
    def get_heatmap_topic_matrix_source(
        self,
        student_ids: tuple[str, ...],
        section_filter: str,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for the student-topic matrix."""

    @abstractmethod
    def get_heatmap_course_topic_matrix_source(
        self,
        student_ids: tuple[str, ...],
        work_ids: tuple[str, ...],
    ) -> HeatmapMatrixSource:
        """Return normalized facts for a course student-topic matrix."""

    @abstractmethod
    def get_heatmap_course_timeline_source(
        self,
        student_ids: tuple[str, ...],
        work_ids: tuple[str, ...],
    ) -> HeatmapCourseTimelineSource:
        """Return normalized facts for a course timeline chart."""

    @abstractmethod
    def get_heatmap_subtopic_matrix_source(
        self,
        student_ids: tuple[str, ...],
        topic_id: str,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for the student-subtopic matrix."""
