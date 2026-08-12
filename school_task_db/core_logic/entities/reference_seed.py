"""Entities for seeding editable fallback reference catalogs."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SimpleReferenceSeedItem:
    category: str
    items_text: str
    is_active: bool = True


@dataclass(frozen=True)
class SubjectReferenceSeedItem:
    subject: str
    grade_level: str
    category: str
    items_text: str
    is_active: bool = True


@dataclass(frozen=True)
class ReferenceSeedDefinition:
    simple_references: Tuple[SimpleReferenceSeedItem, ...] = ()
    subject_references: Tuple[SubjectReferenceSeedItem, ...] = ()


@dataclass(frozen=True)
class SeedReferencesRequest:
    definition: ReferenceSeedDefinition
    replace_existing: bool = False


@dataclass(frozen=True)
class ReferenceSeedMutation:
    reference_type: str
    key: Tuple[str, ...]
    display_name: str
    status: str
    items_count: int


@dataclass(frozen=True)
class SeedReferencesResult:
    mutations: Tuple[ReferenceSeedMutation, ...]

    @property
    def created_count(self) -> int:
        return self._count_status('created')

    @property
    def updated_count(self) -> int:
        return self._count_status('updated')

    @property
    def skipped_count(self) -> int:
        return self._count_status('skipped')

    def _count_status(self, status: str) -> int:
        return sum(item.status == status for item in self.mutations)


class ReferenceSeedValidationError(ValueError):
    """Raised when a reference seed definition is inconsistent."""
