"""Entities for importing a curriculum catalog and codifier bindings."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CurriculumSubtopicImportItem:
    name: str
    order: int


@dataclass(frozen=True)
class CurriculumTopicImportItem:
    section: str
    name: str
    grade_level: int
    order: int
    subtopics: Tuple[CurriculumSubtopicImportItem, ...] = ()


@dataclass(frozen=True)
class CodifierContentBindingItem:
    codifier_short_name: str
    content_code: str
    topic_name: str
    subtopic_name: str = ''


@dataclass(frozen=True)
class CurriculumImportDefinition:
    subject: str
    sections: Tuple[str, ...]
    topics: Tuple[CurriculumTopicImportItem, ...]
    bindings: Tuple[CodifierContentBindingItem, ...] = ()


@dataclass(frozen=True)
class CurriculumImportRequest:
    definition: CurriculumImportDefinition
    clear_existing: bool = False


@dataclass(frozen=True)
class CurriculumBindingIssue:
    reason: str
    codifier_short_name: str
    content_code: str
    topic_name: str = ''
    subtopic_name: str = ''


@dataclass(frozen=True)
class CurriculumImportResult:
    topics_created: int = 0
    subtopics_created: int = 0
    topics_deleted: int = 0
    subtopics_deleted: int = 0
    bindings_applied: int = 0
    bound_codifier_entries: int = 0
    total_codifier_entries: int = 0
    issues: Tuple[CurriculumBindingIssue, ...] = ()


class CurriculumImportValidationError(ValueError):
    """Raised when a curriculum import definition is inconsistent."""
