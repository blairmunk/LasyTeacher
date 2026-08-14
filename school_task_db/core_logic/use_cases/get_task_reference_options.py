"""Build task form reference options."""

from dataclasses import dataclass

from core_logic.entities.task import SelectOption
from core_logic.interfaces.task_taxonomy_repo import ITaskTaxonomyRepository


@dataclass(frozen=True)
class SubtopicOptionsResult:
    subtopics: tuple[SelectOption, ...]

    def __post_init__(self):
        object.__setattr__(self, 'subtopics', tuple(self.subtopics))


class GetSubtopicOptionsUseCase:
    def __init__(self, task_catalog_repo: ITaskTaxonomyRepository):
        self.task_catalog_repo = task_catalog_repo

    def execute(self, topic_id: str) -> SubtopicOptionsResult:
        if not topic_id:
            return SubtopicOptionsResult(subtopics=())
        return SubtopicOptionsResult(
            subtopics=self.task_catalog_repo.get_subtopic_options(topic_id),
        )
