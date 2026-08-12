"""Codifier import entities."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CodifierImportContentItem:
    code: str
    name: str
    parent_code: str = ''
    grade_studied: str = ''


@dataclass(frozen=True)
class CodifierImportRequirementItem:
    code: str
    name: str
    cognitive_level: str = ''


@dataclass(frozen=True)
class CodifierImportDefinition:
    name: str
    short_name: str
    subject: str
    exam_type: str
    year: int
    is_active: bool = True
    content: Tuple[CodifierImportContentItem, ...] = ()
    requirements: Tuple[CodifierImportRequirementItem, ...] = ()


@dataclass(frozen=True)
class ImportCodifierRequest:
    definition: CodifierImportDefinition
    clear_existing: bool = False


@dataclass(frozen=True)
class ImportCodifierResult:
    status: str
    display_name: str = ''
    deleted_count: int = 0
    content_count: int = 0
    requirements_count: int = 0


class CodifierImportValidationError(ValueError):
    """Raised when a codifier import definition is inconsistent."""
