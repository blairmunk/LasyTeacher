"""Read port for variant tasks shown and graded during review."""

from abc import ABC, abstractmethod

from core_logic.entities.review import ReviewVariantTaskRef


class IReviewTaskRepository(ABC):
    @abstractmethod
    def get_variant_tasks(
        self,
        participation_id: str,
    ) -> tuple[ReviewVariantTaskRef, ...]:
        """Return ordered variant task snapshots for one participation."""
