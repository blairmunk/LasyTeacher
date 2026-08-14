"""Core app screen DTOs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SearchTaskResult:
    pk: str
    topic: str
    text: str
    short_uuid: str


@dataclass(frozen=True)
class SearchWorkResult:
    pk: str
    name: str
    work_type_display: str
    duration: int
    short_uuid: str


@dataclass(frozen=True)
class SearchVariantResult:
    pk: str
    display_name: str
    number: int
    task_count: int
    total_max_points: int
    short_uuid: str
    work: Optional["SearchRelatedResult"] = None
    events: tuple["SearchRelatedResult", ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'events', tuple(self.events))

    @property
    def has_work(self) -> bool:
        return self.work is not None


@dataclass(frozen=True)
class SearchGroupResult:
    pk: str
    name: str
    task_count: int
    short_uuid: str


@dataclass(frozen=True)
class SearchRelatedResult:
    pk: str
    name: str


@dataclass(frozen=True)
class SearchStudentResult:
    pk: str
    full_name: str
    short_uuid: str


@dataclass(frozen=True)
class SearchStudentGroupResult:
    pk: str
    name: str
    students_count: int
    short_uuid: str


@dataclass(frozen=True)
class SearchEventResult:
    pk: str
    name: str
    planned_date: Optional[datetime]
    status_display: str
    short_uuid: str


@dataclass(frozen=True)
class SearchTopicResult:
    pk: str
    name: str
    subject: str
    grade_level: int
    short_uuid: str


@dataclass(frozen=True)
class SearchCourseResult:
    pk: str
    name: str
    subject: str
    grade_level: int
    short_uuid: str


@dataclass(frozen=True)
class SearchSourceResult:
    pk: str
    name: str
    short_name: str
    source_type_display: str
    short_uuid: str


@dataclass(frozen=True)
class GlobalSearchResults:
    tasks: tuple[SearchTaskResult, ...] = field(default_factory=tuple)
    works: tuple[SearchWorkResult, ...] = field(default_factory=tuple)
    variants: tuple[SearchVariantResult, ...] = field(default_factory=tuple)
    groups: tuple[SearchGroupResult, ...] = field(default_factory=tuple)
    students: tuple[SearchStudentResult, ...] = field(default_factory=tuple)
    student_groups: tuple[SearchStudentGroupResult, ...] = field(
        default_factory=tuple,
    )
    events: tuple[SearchEventResult, ...] = field(default_factory=tuple)
    topics: tuple[SearchTopicResult, ...] = field(default_factory=tuple)
    courses: tuple[SearchCourseResult, ...] = field(default_factory=tuple)
    sources: tuple[SearchSourceResult, ...] = field(default_factory=tuple)

    def __post_init__(self):
        for field_name in self.__dataclass_fields__:
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))

    @property
    def total_count(self) -> int:
        return sum(
            len(getattr(self, field_name))
            for field_name in self.__dataclass_fields__
        )


@dataclass(frozen=True)
class ImportLogItem:
    filename: str
    mode_display: str
    dry_run: bool
    tasks_created: int
    tasks_updated: int
    tasks_skipped: int
    errors_count: int
    duration_ms: int
    duration_human: str
    file_size_human: str
    status_icon: str
    created_at: datetime


@dataclass(frozen=True)
class DashboardSummaryData:
    tasks_count: int = 0
    works_count: int = 0
    variants_count: int = 0
    orphan_variants_count: int = 0
    students_count: int = 0
    events_count: int = 0
    groups_count: int = 0


@dataclass(frozen=True)
class GlobalSearchData:
    query: str = ''
    results: GlobalSearchResults = field(default_factory=GlobalSearchResults)
    total_found: int = 0
    search_mode: Optional[str] = None
    found_text: str = ''

@dataclass(frozen=True)
class ImportPageData:
    recent_imports: List[ImportLogItem] = field(default_factory=list)


@dataclass(frozen=True)
class ImportHistoryData:
    imports: List[ImportLogItem] = field(default_factory=list)


@dataclass(frozen=True)
class ImportJsonValidationData:
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': self.summary,
        }
