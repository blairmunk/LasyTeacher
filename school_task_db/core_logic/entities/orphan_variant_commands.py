"""Command data for attaching orphan variants to a new work."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateWorkFromOrphanVariantsParams:
    name: str
    work_type: str
    max_score: int
    variant_ids: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'variant_ids', tuple(self.variant_ids))


@dataclass(frozen=True)
class CreatedWorkFromOrphanVariantsRef:
    work_id: str
    variant_count: int
