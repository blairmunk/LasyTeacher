"""Persistence port for restoring a work specification from variants."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work_spec_sync import (
    WorkSpecSyncItem,
    WorkSpecSyncSaveResult,
    WorkSpecSyncSource,
)


class IWorkSpecSyncRepository(ABC):
    @abstractmethod
    def get_work_spec_sync_source(
        self,
        work_id: str,
    ) -> Optional[WorkSpecSyncSource]:
        """Return variant group snapshots used to restore a specification."""

    @abstractmethod
    def save_work_spec_sync_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: tuple[WorkSpecSyncItem, ...],
    ) -> WorkSpecSyncSaveResult:
        """Persist a sync plan if its variant source is still current."""
