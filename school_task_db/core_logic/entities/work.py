"""Work screen DTOs."""

from dataclasses import dataclass, field
from typing import Any, List


@dataclass(frozen=True)
class WorkDetailData:
    variants: Any
    analog_groups: List[Any] = field(default_factory=list)
    spec_preview: List[Any] = field(default_factory=list)
    show_sync_button: bool = False


@dataclass(frozen=True)
class WorkListData:
    works: Any


@dataclass(frozen=True)
class VariantListData:
    variants: Any


@dataclass(frozen=True)
class WorkFormData:
    analog_group_options: Any


@dataclass(frozen=True)
class VariantDetailData:
    variant_tasks: Any
    total_max_points: int = 0


@dataclass(frozen=True)
class VariantGenerationInfo:
    number: int
    work_name: str


@dataclass(frozen=True)
class VariantGenerationPlaceholderResult:
    status: str
    message: str = ''


@dataclass(frozen=True)
class RemedialOriginalTaskRow:
    task: Any
    order: int
    points: Any
    max_points: Any
    pct: float
    status: str
    group_name: str = ''


@dataclass(frozen=True)
class RemedialSheetData:
    variant: Any
    student: Any
    source_work: Any
    mark: Any
    original_tasks: List[RemedialOriginalTaskRow] = field(default_factory=list)
    new_tasks: Any = None


@dataclass(frozen=True)
class OrphanVariantListData:
    variants: Any
    total_orphans: int = 0


@dataclass(frozen=True)
class SyncWorkAnalogGroupsResult:
    created_count: int


@dataclass(frozen=True)
class GenerateWorkVariantsResult:
    created_count: int


@dataclass(frozen=True)
class OrphanVariantRef:
    pk: str
    variant_type: str
    total_max_points: int


@dataclass(frozen=True)
class CreateWorkFromOrphansResult:
    status: str
    work_id: str = ''
    work_name: str = ''
    variant_count: int = 0


@dataclass(frozen=True)
class VariantDeleteInfo:
    task_count: int
    participation_count: int = 0

    @property
    def has_participations(self) -> bool:
        return self.participation_count > 0


@dataclass(frozen=True)
class DeleteVariantResult:
    status: str
    redirect_work_id: str = ''
    variant_short_id: str = ''
    participation_count: int = 0


@dataclass(frozen=True)
class BulkDeleteVariantsResult:
    status: str
    deleted_count: int = 0
    remaining_count: int = 0
