"""Read port for task topics, sources, subtopics and types."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core_logic.entities.task import SelectOption


class ITaskTaxonomyRepository(ABC):
    @abstractmethod
    def get_subtopic_topic_id(self, subtopic_id: str) -> Optional[str]:
        """Return the parent topic ID for a subtopic, or None."""

    @abstractmethod
    def get_list_topics(self) -> List[SelectOption]:
        """Return topic options for task screens."""

    @abstractmethod
    def get_list_sources(self) -> List[SelectOption]:
        """Return task source options."""

    @abstractmethod
    def get_subtopics_for_topic(self, topic_id: str) -> List[SelectOption]:
        """Return subtopic options for task list filtering."""

    @abstractmethod
    def get_subtopic_options(self, topic_id: str) -> List[SelectOption]:
        """Return subtopic options for task editing."""

    @abstractmethod
    def get_task_type_choices(self) -> List[Tuple[str, str]]:
        """Return canonical task type choices."""
