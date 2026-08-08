"""Port for heatmap report data."""

from abc import ABC, abstractmethod
from typing import Any

from core_logic.entities.heatmap import (
    HeatmapCourseOverviewData,
    HeatmapCourseTimelineSource,
    HeatmapDrilldownOverviewData,
    HeatmapMatrixSource,
    HeatmapOverviewData,
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
)


class IHeatmapRepository(ABC):
    @abstractmethod
    def get_heatmap_overview(self, group_id: Any) -> HeatmapOverviewData:
        """Return base heatmap data."""

    @abstractmethod
    def get_heatmap_topic_matrix_source(
        self,
        student_ids: list,
        section_filter: str,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for the student-topic matrix."""

    @abstractmethod
    def get_heatmap_course_overview(
        self,
        course_id: Any,
        group_id: Any,
    ) -> HeatmapCourseOverviewData:
        """Return base course heatmap data."""

    @abstractmethod
    def get_heatmap_course_topic_matrix_source(
        self,
        student_ids: list,
        work_ids: list,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for a course student-topic matrix."""

    @abstractmethod
    def get_heatmap_course_timeline_source(
        self,
        student_ids: list,
        work_ids: list,
    ) -> HeatmapCourseTimelineSource:
        """Return normalized facts for a course timeline chart."""

    @abstractmethod
    def get_heatmap_drilldown_overview(
        self,
        topic_id: Any,
        group_id: Any,
    ) -> HeatmapDrilldownOverviewData:
        """Return base topic drilldown heatmap data."""

    @abstractmethod
    def get_heatmap_subtopic_matrix_source(
        self,
        student_ids: list,
        topic_id: Any,
    ) -> HeatmapMatrixSource:
        """Return normalized facts for the student-subtopic matrix."""

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
