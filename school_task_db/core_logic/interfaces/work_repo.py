"""Work repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Set

from core_logic.entities.work import (
    OrphanVariantRef,
    RemedialSheetData,
    WorkDetailSpecGroup,
    WorkDetailSpecPreviewItem,
    WorkDetailVariant,
    WorkDetailWork,
    WorkListItem,
    VariantGenerationInfo,
    VariantDeleteInfo,
    VariantDetailTaskRow,
    VariantDetailVariant,
)


@dataclass(frozen=True)
class CreateWorkParams:
    name: str
    work_type: str = 'remedial'
    max_score: int = 0
    variant_counter: int = 0


@dataclass(frozen=True)
class CreateVariantParams:
    work_id: Optional[str]
    number: int
    student_id: str
    task_ids: List[str]
    work_name_snapshot: str
    max_score_snapshot: int
    source_work_id: Optional[str] = None
    variant_type: str = 'remedial'


@dataclass(frozen=True)
class AttachVariantsToWorkParams:
    work_id: str
    variant_ids: List[str]
    work_name_snapshot: str
    max_score_snapshot: int


@dataclass(frozen=True)
class CreateWorkAnalogGroupParams:
    work_id: str
    analog_group_id: str
    order: int
    count: int
    weight: int


@dataclass(frozen=True)
class CreateWorkWithVariantFromTasksParams:
    name: str
    work_type: str
    task_ids: List[str]


@dataclass(frozen=True)
class CreatedWorkVariantRef:
    work_id: str
    variant_id: str
    tasks_count: int


class IWorkRepository(ABC):
    @abstractmethod
    def get_list_works(self) -> List[WorkListItem]:
        """Return works for the work list page."""

    @abstractmethod
    def get_list_variants(self) -> Any:
        """Return variants for the variant list page."""

    @abstractmethod
    def get_work_form_analog_group_options(self) -> Any:
        """Return analog group options for the work form page."""

    @abstractmethod
    def get_work_name(self, work_id: str) -> Optional[str]:
        """Return a work name, or None when the work does not exist."""

    @abstractmethod
    def get_work_generation_target(self, work_id: str) -> Any:
        """Return a work for the variant generation form."""

    @abstractmethod
    def get_work_detail(self, work_id: str) -> Optional[WorkDetailWork]:
        """Return one work detail read model, or None."""

    @abstractmethod
    def get_detail_variants(self, work_id: str) -> List[WorkDetailVariant]:
        """Return variant read models for the work detail page."""

    @abstractmethod
    def get_detail_analog_groups(self, work_id: str) -> List[WorkDetailSpecGroup]:
        """Return work specification read models for the work detail page."""

    @abstractmethod
    def get_spec_preview(self, work_id: str) -> List[WorkDetailSpecPreviewItem]:
        """Return points specification preview read models for the work detail page."""

    @abstractmethod
    def get_variant_detail(self, variant_id: str) -> Optional[VariantDetailVariant]:
        """Return one variant detail read model, or None."""

    @abstractmethod
    def get_variant_detail_tasks(self, variant_id: str) -> List[VariantDetailTaskRow]:
        """Return ordered task read models for the variant detail page."""

    @abstractmethod
    def get_variant_total_max_points(self, variant_id: str) -> int:
        """Return total max points for a variant."""

    @abstractmethod
    def get_variant_type(self, variant_id: str) -> Optional[str]:
        """Return variant type, or None when the variant does not exist."""

    @abstractmethod
    def get_variant_generation_info(
        self,
        variant_id: str,
    ) -> Optional[VariantGenerationInfo]:
        """Return variant info for variant document generation."""

    @abstractmethod
    def get_remedial_sheet_data(self, variant_id: str) -> RemedialSheetData:
        """Return data for rendering a remedial sheet."""

    @abstractmethod
    def get_orphan_variants(self) -> Any:
        """Return orphan variants for the orphan list page."""

    @abstractmethod
    def count_orphan_variants(self) -> int:
        """Return orphan variant count."""

    @abstractmethod
    def sync_analog_groups_from_variants(self, work_id: str) -> int:
        """Sync work analog groups from existing variants and return created count."""

    @abstractmethod
    def generate_variants(self, work_id: str, count: int) -> int:
        """Generate variants for a work and return created count."""

    @abstractmethod
    def get_orphan_variant_refs(self, variant_ids: List[str]) -> List[OrphanVariantRef]:
        """Return selected orphan variant refs ordered for attaching to work."""

    @abstractmethod
    def attach_variants_to_work(self, params: AttachVariantsToWorkParams) -> int:
        """Attach variants to a work and return attached count."""

    @abstractmethod
    def get_variant_delete_info(self, variant_id: str) -> VariantDeleteInfo:
        """Return delete screen information for a variant."""

    @abstractmethod
    def detach_variant_from_work(self, variant_id: str) -> str:
        """Detach a variant from its work and return the variant short ID."""

    @abstractmethod
    def delete_variant(self, variant_id: str) -> str:
        """Delete a variant and return its previous work ID, if any."""

    @abstractmethod
    def bulk_delete_work_variants(self, work_id: str, variant_ids: List[str]) -> int:
        """Delete selected variants of a work and return deleted object count."""

    @abstractmethod
    def count_work_variants(self, work_id: str) -> int:
        """Return variant count for a work."""

    @abstractmethod
    def get_variant_task_ids(self, work_id: str) -> Set[str]:
        """Return task IDs used in all variants of a work."""

    @abstractmethod
    def get_student_variant_task_ids(
        self,
        work_id: str,
        student_id: str,
        event_id: str,
    ) -> Set[str]:
        """Return task IDs from a concrete student's variant for an event."""

    @abstractmethod
    def create_work(self, params: CreateWorkParams) -> str:
        """Create a work and return its ID."""

    @abstractmethod
    def create_work_analog_group(self, params: CreateWorkAnalogGroupParams) -> None:
        """Create one work analog-group specification row."""

    @abstractmethod
    def create_variant_with_tasks(self, params: CreateVariantParams) -> str:
        """Create a variant with VariantTask rows and return the variant ID."""

    @abstractmethod
    def create_work_with_variant_from_tasks(
        self,
        params: CreateWorkWithVariantFromTasksParams,
    ) -> CreatedWorkVariantRef:
        """Create a work and its first variant from selected tasks."""
