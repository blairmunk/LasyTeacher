"""Build topic list screen data."""

from core_logic.entities.curriculum import TopicListData
from core_logic.interfaces.curriculum_repo import ICurriculumRepository


class GetTopicListUseCase:
    def __init__(self, curriculum_repo: ICurriculumRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self) -> TopicListData:
        return TopicListData(topics=self.curriculum_repo.get_topics())
