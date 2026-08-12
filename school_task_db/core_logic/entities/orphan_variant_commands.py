"""Command data for attaching orphan variants to a new work."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CreateWorkFromOrphanVariantsParams:
    name: str
    work_type: str
    max_score: int
    variant_ids: List[str]


@dataclass(frozen=True)
class CreatedWorkFromOrphanVariantsRef:
    work_id: str
    variant_count: int
