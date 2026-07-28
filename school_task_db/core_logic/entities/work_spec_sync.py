"""Data contracts for restoring a work specification from variants."""

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class WorkSpecSyncItem:
    analog_group_id: str
    count: int
    order: int


@dataclass(frozen=True)
class WorkSpecSyncSource:
    variant_counter: int
    variant_group_ids: Tuple[Tuple[str, ...], ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(
            self,
            'variant_group_ids',
            tuple(tuple(group_ids) for group_ids in self.variant_group_ids),
        )


@dataclass(frozen=True)
class WorkSpecSyncSaveResult:
    status: str
    created_count: int = 0

