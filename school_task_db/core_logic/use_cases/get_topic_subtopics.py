"""Build serialized subtopic options for one topic."""

from dataclasses import dataclass

from core_logic.entities.curriculum import TopicSubtopicsData
from core_logic.interfaces.topic_catalog_repo import ITopicCatalogRepository


@dataclass(frozen=True)
class TopicSubtopicsRequest:
    topic_id: str


class GetTopicSubtopicsUseCase:
    def __init__(self, curriculum_repo: ITopicCatalogRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self, request: TopicSubtopicsRequest) -> TopicSubtopicsData:
        return TopicSubtopicsData(
            subtopics=tuple(
                self.curriculum_repo.get_topic_subtopics(
                    topic_id=request.topic_id,
                )
            ),
        )
