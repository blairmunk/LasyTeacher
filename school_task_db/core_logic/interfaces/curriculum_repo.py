"""Curriculum repository interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from core_logic.entities.curriculum import (
    CourseDetailAssignment,
    CourseDetailCourse,
    CourseDetailWorkGroup,
    CourseListItem,
)


class ICurriculumRepository(ABC):
    @abstractmethod
    def get_courses(self) -> List[CourseListItem]:
        """Return courses for the course list page."""

    @abstractmethod
    def get_course(self, course_id: str) -> Optional[CourseDetailCourse]:
        """Return one course detail read model by id or None."""

    @abstractmethod
    def get_course_assignments(self, course_id: str) -> List[CourseDetailAssignment]:
        """Return ordered assignment read models for one course."""

    @abstractmethod
    def get_work_analog_groups(self, work_id: str) -> List[CourseDetailWorkGroup]:
        """Return analog group specs read models for one work."""

    @abstractmethod
    def count_work_variants(self, work_id: str) -> int:
        """Return variant count for one work."""

    @abstractmethod
    def get_topic_subtopics(self, topic_id: str) -> list:
        """Return serialized subtopics for one topic."""
