"""Build task form reference options."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.task import ReferenceElementOption, SelectOption
from core_logic.interfaces.task_catalog_repo import ITaskCatalogRepository


@dataclass(frozen=True)
class SubtopicOptionsResult:
    subtopics: List[SelectOption]


class GetSubtopicOptionsUseCase:
    def __init__(self, task_catalog_repo: ITaskCatalogRepository):
        self.task_catalog_repo = task_catalog_repo

    def execute(self, topic_id: str) -> SubtopicOptionsResult:
        if not topic_id:
            return SubtopicOptionsResult(subtopics=[])
        return SubtopicOptionsResult(
            subtopics=self.task_catalog_repo.get_subtopic_options(topic_id),
        )


@dataclass(frozen=True)
class CodifierElementsResult:
    elements: List[ReferenceElementOption]


class GetCodifierElementsUseCase:
    def __init__(self, task_catalog_repo: ITaskCatalogRepository):
        self.task_catalog_repo = task_catalog_repo

    def execute(self, subject: str, category: str) -> CodifierElementsResult:
        return CodifierElementsResult(
            elements=self.task_catalog_repo.get_reference_element_options(
                subject=subject,
                category=category,
            ),
        )
