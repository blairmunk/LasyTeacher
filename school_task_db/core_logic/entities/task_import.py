"""Task import DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence


@dataclass(frozen=True)
class TaskImportRequest:
    data: Dict[str, Any]
    filename: str
    file_size: int
    mode: str = 'update'
    dry_run: bool = False
    create_missing: bool = True


@dataclass(frozen=True)
class TaskImportPreviewRequest:
    data: Dict[str, Any]


@dataclass(frozen=True)
class TaskImportFileRequest:
    filename: str
    file_size: int
    content: bytes


@dataclass(frozen=True)
class TaskImportFileResult:
    filename: str = ''
    file_size: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    error: str = ''

    @property
    def success(self) -> bool:
        return not self.error


@dataclass(frozen=True)
class TaskImportExecutionSubmissionRequest:
    filename: str
    file_size: int
    content: bytes
    form_data: Mapping[str, Sequence[str]]


@dataclass(frozen=True)
class TaskImportExecutionSubmissionResult:
    import_request: Optional[TaskImportRequest] = None
    error: str = ''

    @property
    def success(self) -> bool:
        return self.import_request is not None and not self.error


@dataclass(frozen=True)
class TaskImportPreviewResult:
    preview: Dict[str, Any] = None
    warning: str = ''

    @property
    def success(self) -> bool:
        return not self.warning


@dataclass(frozen=True)
class TaskImportValidationPreviewResult:
    filename: str = ''
    file_size: int = 0
    validation: Dict[str, Any] = field(default_factory=dict)
    preview: Optional[Dict[str, Any]] = None
    error: str = ''

    @property
    def success(self) -> bool:
        return not self.error

    def to_response_data(self) -> Dict[str, Any]:
        if not self.success:
            return {'error': self.error}

        return {
            'filename': self.filename,
            'file_size': self.file_size,
            'validation': self.validation,
            'preview': self.preview,
        }


@dataclass(frozen=True)
class TaskImportSampleData:
    filename: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class TaskImportResult:
    status: str
    dry_run: bool = False
    log_id: str = ''
    duration_ms: int = 0
    stats: Dict[str, Any] = field(default_factory=dict)
    message: str = ''
    error: str = ''

    @property
    def success(self) -> bool:
        return self.status == 'success'

    def to_response_data(self) -> Dict[str, Any]:
        if not self.success:
            return {
                'status': self.status,
                'log_id': self.log_id,
                'error': self.error,
            }

        return {
            'status': self.status,
            'dry_run': self.dry_run,
            'log_id': self.log_id,
            'duration_ms': self.duration_ms,
            'stats': self.stats,
            'message': self.message,
        }


@dataclass(frozen=True)
class TaskImportRunSummary:
    created_by_type: Mapping[str, int] = field(default_factory=dict)
    updated_by_type: Mapping[str, int] = field(default_factory=dict)
    skipped_by_type: Mapping[str, int] = field(default_factory=dict)
    errors: int = 0
    error_messages: tuple[str, ...] = field(default_factory=tuple)
    context_counts: Mapping[str, int] = field(default_factory=dict)
    preview: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        for field_name in (
            'created_by_type',
            'updated_by_type',
            'skipped_by_type',
            'context_counts',
            'preview',
        ):
            object.__setattr__(self, field_name, dict(getattr(self, field_name)))
        object.__setattr__(self, 'error_messages', tuple(self.error_messages))

    @property
    def tasks_created(self) -> int:
        return self.created_by_type.get('tasks', 0)

    @property
    def tasks_updated(self) -> int:
        return self.updated_by_type.get('tasks', 0)

    @property
    def tasks_skipped(self) -> int:
        return self.skipped_by_type.get('tasks', 0)

    @property
    def status(self) -> str:
        return 'partial' if self.errors else 'success'

    def operation_counts(self) -> Dict[str, Dict[str, int]]:
        return {
            'created': dict(self.created_by_type),
            'updated': dict(self.updated_by_type),
            'skipped': dict(self.skipped_by_type),
        }

    def to_stats(self) -> Dict[str, Any]:
        context = dict(self.context_counts)
        return {
            'created': self.tasks_created,
            'updated': self.tasks_updated,
            'skipped': self.tasks_skipped,
            'errors': self.errors,
            'by_type': self.operation_counts(),
            'context': context,
            'context_counts': dict(context),
            'preview': dict(self.preview),
        }


@dataclass(frozen=True, order=True)
class TaskImportClassificationKey:
    kind: str
    subject: str
    exam_type: str
    year: int
    code: str


@dataclass(frozen=True)
class TaskImportPreviewLookup:
    task_ids: tuple[str, ...] = field(default_factory=tuple)
    group_ids: tuple[str, ...] = field(default_factory=tuple)
    topic_ids: tuple[str, ...] = field(default_factory=tuple)
    subtopic_ids: tuple[str, ...] = field(default_factory=tuple)
    classifications: tuple[TaskImportClassificationKey, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        for field_name in (
            'task_ids',
            'group_ids',
            'topic_ids',
            'subtopic_ids',
            'classifications',
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))


@dataclass(frozen=True)
class TaskImportPreviewFacts:
    existing_task_ids: frozenset[str] = field(default_factory=frozenset)
    existing_group_ids: frozenset[str] = field(default_factory=frozenset)
    existing_topic_ids: frozenset[str] = field(default_factory=frozenset)
    subtopic_topic_ids: Mapping[str, str] = field(default_factory=dict)
    existing_classifications: frozenset[TaskImportClassificationKey] = field(
        default_factory=frozenset,
    )

    def __post_init__(self):
        for field_name in (
            'existing_task_ids',
            'existing_group_ids',
            'existing_topic_ids',
            'existing_classifications',
        ):
            object.__setattr__(
                self,
                field_name,
                frozenset(getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            'subtopic_topic_ids',
            dict(self.subtopic_topic_ids),
        )
