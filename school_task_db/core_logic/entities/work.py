"""Work screen DTOs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional


@dataclass(frozen=True)
class WorkDetailData:
    work: Optional["WorkDetailWork"] = None
    variants: List["WorkDetailVariant"] = field(default_factory=list)
    analog_groups: List["WorkDetailSpecGroup"] = field(default_factory=list)
    spec_preview: List["WorkDetailSpecPreviewItem"] = field(default_factory=list)
    show_sync_button: bool = False


@dataclass(frozen=True)
class WorkDetailWork:
    pk: str
    name: str
    work_type: str
    work_type_display: str
    duration: int
    max_score: int
    effective_max_score: int
    variant_count: int
    created_at: datetime
    updated_at: datetime

    @property
    def id(self) -> str:
        return self.pk


@dataclass(frozen=True)
class WorkDetailAnalogGroup:
    pk: str
    name: str
    task_count: int = 0


@dataclass(frozen=True)
class WorkDetailSpecGroup:
    order: int
    analog_group: WorkDetailAnalogGroup
    count: int
    weight: int


@dataclass(frozen=True)
class WorkDetailSpecPreviewItem:
    wg: WorkDetailSpecGroup
    per_task: int
    total_points: int
    available_count: int = 0


@dataclass(frozen=True)
class WorkDetailVariant:
    pk: str
    number: int
    short_uuid: str
    task_count: int
    total_max_points: int
    created_at: datetime
    variant_type: str
    has_assigned_student: bool = False

    @property
    def id(self) -> str:
        return self.pk


@dataclass(frozen=True)
class WorkListData:
    works: List["WorkListItem"]


@dataclass(frozen=True)
class WorkListItem:
    pk: str
    name: str
    duration: int
    created_at: datetime
    variant_count: int = 0


@dataclass(frozen=True)
class VariantListData:
    variants: List["VariantListItem"]


@dataclass(frozen=True)
class VariantListWorkRef:
    pk: str
    name: str
    duration: int


@dataclass(frozen=True)
class VariantListItem:
    pk: str
    number: int
    created_at: datetime
    task_count: int = 0
    work: Optional[VariantListWorkRef] = None


@dataclass(frozen=True)
class WorkFormData:
    analog_group_options: Any


@dataclass(frozen=True)
class VariantGenerationFormData:
    work: Optional["VariantGenerationWork"] = None
    work_groups: List["VariantGenerationGroup"] = field(default_factory=list)
    status: str = 'ready'


@dataclass(frozen=True)
class VariantGenerationWork:
    pk: str
    name: str
    duration: int
    variant_counter: int


@dataclass(frozen=True)
class VariantGenerationGroup:
    group_name: str
    requested_count: int
    available_count: int


@dataclass(frozen=True)
class VariantDetailData:
    variant: Optional["VariantDetailVariant"] = None
    variant_tasks: List["VariantDetailTaskRow"] = field(default_factory=list)
    total_max_points: int = 0


@dataclass(frozen=True)
class VariantDetailRef:
    pk: str
    name: str = ''
    short_uuid: str = ''


@dataclass(frozen=True)
class VariantDetailStudentRef:
    pk: str
    full_name: str = ''
    short_name: str = ''


@dataclass(frozen=True)
class VariantDetailVariant:
    pk: str
    number: int
    display_name: str
    short_uuid: str
    medium_uuid: str
    variant_type: str
    variant_type_display: str
    display_duration: int
    display_max_score: int
    created_at: datetime
    work: Optional[VariantDetailRef] = None
    assigned_student: Optional[VariantDetailStudentRef] = None
    source_work: Optional[VariantDetailRef] = None

    @property
    def id(self) -> str:
        return self.pk


@dataclass(frozen=True)
class VariantDetailImage:
    caption: str = ''
    position: str = ''
    safe_url: Optional[str] = None
    css_class: str = 'task-image-bottom-70'


@dataclass(frozen=True)
class VariantDetailTask:
    pk: str
    id: str
    topic: str
    text: str
    answer: str
    task_type_display: str
    difficulty: int
    short_uuid: str
    images: List[VariantDetailImage] = field(default_factory=list)


@dataclass(frozen=True)
class VariantDetailTaskRow:
    task: VariantDetailTask
    order: int
    max_points: int


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
    status: str = 'ready'
    message: str = ''
    redirect_work_id: str = ''


@dataclass(frozen=True)
class OrphanVariantListData:
    variants: List["OrphanVariantListItem"]
    total_orphans: int = 0


@dataclass(frozen=True)
class OrphanVariantStudentRef:
    pk: str
    short_name: str


@dataclass(frozen=True)
class OrphanVariantListItem:
    pk: str
    display_name: str
    short_uuid: str
    variant_type: str
    task_count: int
    total_max_points: int
    created_at: datetime
    assigned_student: Optional[OrphanVariantStudentRef] = None


@dataclass(frozen=True)
class SyncWorkAnalogGroupsResult:
    created_count: int
    status: str = 'synced'


@dataclass(frozen=True)
class ComposeWorkVariantsResult:
    created_count: int
    status: str = 'generated'


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
    display_name: str = ''
    short_uuid: str = ''
    work_id: str = ''
    work_name: str = ''
    total_max_points: int = 0

    @property
    def has_participations(self) -> bool:
        return self.participation_count > 0

    @property
    def has_work(self) -> bool:
        return bool(self.work_id)


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
