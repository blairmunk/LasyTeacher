"""Build topic list screen data."""

from core_logic.entities.curriculum import TopicListData
from core_logic.interfaces.topic_catalog_repo import ITopicCatalogRepository


class GetTopicListUseCase:
    def __init__(self, curriculum_repo: ITopicCatalogRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self) -> TopicListData:
        return TopicListData(topics=self.curriculum_repo.get_topics())
