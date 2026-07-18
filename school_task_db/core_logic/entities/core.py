"""Core app screen DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    has_work: bool = False


@dataclass(frozen=True)
class SearchGroupResult:
    pk: str
    name: str
    task_count: int
    short_uuid: str


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
    created_at: Any


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
    results: Dict[str, Any] = None
    total_found: int = 0
    search_mode: Optional[str] = None
    found_text: str = ''

    def __post_init__(self):
        if self.results is None:
            object.__setattr__(self, 'results', {})


@dataclass(frozen=True)
class ImportPageData:
    recent_imports: Any


@dataclass(frozen=True)
class ImportHistoryData:
    imports: Any


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
