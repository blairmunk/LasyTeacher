"""Build topic detail screen data."""

from core_logic.entities.curriculum import TopicDetailData
from core_logic.interfaces.topic_catalog_repo import ITopicCatalogRepository


class GetTopicDetailUseCase:
    def __init__(self, curriculum_repo: ITopicCatalogRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self, topic_id: str) -> TopicDetailData:
        topic = self.curriculum_repo.get_topic(topic_id)
        if topic is None:
            return TopicDetailData()

        return TopicDetailData(
            topic=topic,
            subtopics=tuple(
                self.curriculum_repo.get_topic_detail_subtopics(topic_id),
            ),
        )
