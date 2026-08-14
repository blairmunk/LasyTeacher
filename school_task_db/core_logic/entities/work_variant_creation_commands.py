"""Command data for persisting new work variants."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.work_specification_commands import CreateWorkParams
from core_logic.entities.work_variant_composition import VariantCreationPlan


@dataclass(frozen=True)
class CreateVariantParams:
    work_id: Optional[str]
    student_id: str
    plan: VariantCreationPlan
    source_work_id: Optional[str] = None
    source_participation_id: Optional[str] = None
    source_attempt_snapshot_id: Optional[str] = None
    variant_type: str = 'remedial'


@dataclass(frozen=True)
class NewWorkVariantParams:
    student_id: str
    plan: VariantCreationPlan
    source_work_id: Optional[str] = None
    source_participation_id: Optional[str] = None
    source_attempt_snapshot_id: Optional[str] = None
    variant_type: str = 'remedial'


@dataclass(frozen=True)
class CreateWorkWithVariantsParams:
    work: CreateWorkParams
    variants: tuple[NewWorkVariantParams, ...]

    def __post_init__(self):
        object.__setattr__(self, 'variants', tuple(self.variants))


@dataclass(frozen=True)
class CreatedWorkWithVariantsRef:
    work_id: str
    variant_ids: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'variant_ids', tuple(self.variant_ids))


@dataclass(frozen=True)
class CreateWorkWithVariantFromTasksParams:
    name: str
    work_type: str
    task_ids: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'task_ids', tuple(self.task_ids))


@dataclass(frozen=True)
class CreatedWorkVariantRef:
    work_id: str
    variant_id: str
    tasks_count: int
