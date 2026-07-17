"""Build serialized subtopic options for one topic."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.curriculum import TopicSubtopicsData
from core_logic.interfaces.curriculum_repo import ICurriculumRepository


@dataclass(frozen=True)
class TopicSubtopicsRequest:
    topic_id: Any


class GetTopicSubtopicsUseCase:
    def __init__(self, curriculum_repo: ICurriculumRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self, request: TopicSubtopicsRequest) -> TopicSubtopicsData:
        return TopicSubtopicsData(
            subtopics=self.curriculum_repo.get_topic_subtopics(
                topic_id=str(request.topic_id),
            ),
        )
