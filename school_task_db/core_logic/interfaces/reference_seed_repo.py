"""Persistence port for editable reference catalog seeds."""

from abc import ABC, abstractmethod

from core_logic.entities.reference_seed import (
    ReferenceSeedMutation,
    SimpleReferenceSeedItem,
    SubjectReferenceSeedItem,
)


class IReferenceSeedRepository(ABC):
    @abstractmethod
    def seed_simple_reference(
        self,
        item: SimpleReferenceSeedItem,
        replace_existing: bool,
    ) -> ReferenceSeedMutation:
        """Create, replace, or skip one simple reference."""

    @abstractmethod
    def seed_subject_reference(
        self,
        item: SubjectReferenceSeedItem,
        replace_existing: bool,
    ) -> ReferenceSeedMutation:
        """Create, replace, or skip one subject reference."""
