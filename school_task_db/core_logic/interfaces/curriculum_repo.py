"""Curriculum repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICurriculumRepository(ABC):
    @abstractmethod
    def get_course(self, course_id: str) -> Any:
        """Return one course by id or None."""

    @abstractmethod
    def get_course_assignments(self, course_id: str) -> Any:
        """Return ordered assignments for one course."""

    @abstractmethod
    def get_work_analog_groups(self, work_id: str) -> Any:
        """Return analog group specs for one work."""

    @abstractmethod
    def count_work_variants(self, work_id: str) -> int:
        """Return variant count for one work."""

    @abstractmethod
    def get_topic_subtopics(self, topic_id: str) -> list:
        """Return serialized subtopics for one topic."""
