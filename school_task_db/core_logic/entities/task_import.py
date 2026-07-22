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
