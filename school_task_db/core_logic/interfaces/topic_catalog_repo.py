"""Read port for curriculum topics and subtopics."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.curriculum import (
    TopicDetailSubtopic,
    TopicDetailTopic,
    TopicListItem,
)


class ITopicCatalogRepository(ABC):
    @abstractmethod
    def get_topics(self) -> List[TopicListItem]:
        """Return topics for the topic list page."""

    @abstractmethod
    def get_topic(self, topic_id: str) -> Optional[TopicDetailTopic]:
        """Return one topic detail read model by id or None."""

    @abstractmethod
    def get_topic_detail_subtopics(
        self,
        topic_id: str,
    ) -> List[TopicDetailSubtopic]:
        """Return ordered subtopics for one topic detail page."""

    @abstractmethod
    def get_topic_subtopics(self, topic_id: str) -> list:
        """Return serialized subtopics for dependent form fields."""
