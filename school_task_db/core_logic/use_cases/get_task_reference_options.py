"""Build task form reference options."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.task import SelectOption
from core_logic.interfaces.task_taxonomy_repo import ITaskTaxonomyRepository


@dataclass(frozen=True)
class SubtopicOptionsResult:
    subtopics: List[SelectOption]


class GetSubtopicOptionsUseCase:
    def __init__(self, task_catalog_repo: ITaskTaxonomyRepository):
        self.task_catalog_repo = task_catalog_repo

    def execute(self, topic_id: str) -> SubtopicOptionsResult:
        if not topic_id:
            return SubtopicOptionsResult(subtopics=[])
        return SubtopicOptionsResult(
            subtopics=self.task_catalog_repo.get_subtopic_options(topic_id),
        )
