"""Persistence port for legacy task classification backfills."""

from abc import ABC, abstractmethod

from core_logic.entities.task_classification_backfill import (
    TaskClassificationBackfillPlan,
    TaskClassificationBackfillSnapshot,
)


class ITaskClassificationBackfillRepository(ABC):
    @abstractmethod
    def get_backfill_snapshot(self) -> TaskClassificationBackfillSnapshot:
        """Return clean legacy tasks and available classifications."""

    @abstractmethod
    def apply_backfill_plan(self, plan: TaskClassificationBackfillPlan) -> None:
        """Apply a previously prepared conservative backfill plan."""
