"""Document rendering DTOs."""

from dataclasses import dataclass, field
from typing import Optional


DOCUMENT_RENDER_STATUS_GENERATED = 'generated'
DOCUMENT_RENDER_STATUS_NOT_FOUND = 'not_found'
DOCUMENT_RENDER_STATUS_NOT_REMEDIAL = 'not_remedial'
DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED = 'not_personalized'
DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED = (
    'personal_remedial_required'
)
DOCUMENT_RENDER_STATUS_VARIANTS_NOT_REQUIRED = 'variants_not_required'
DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER = 'unsupported_renderer'
DOCUMENT_RENDER_STATUS_EMPTY = 'empty'

GENERATED_FILE_STATUS_READY = 'ready'
GENERATED_FILE_STATUS_NOT_FOUND = 'not_found'
GENERATED_FILE_STATUS_UNSUPPORTED_TYPE = 'unsupported_type'
GENERATED_FILE_STATUS_READ_ERROR = 'read_error'


@dataclass(frozen=True)
class GeneratedDocumentFile:
    filename: str
    size_kb: float


@dataclass(frozen=True)
class GeneratedDocument:
    file_type: str
    files: tuple[GeneratedDocumentFile, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, 'files', tuple(self.files))


@dataclass(frozen=True)
class DocumentRenderResult:
    status: str
    renderer_type: str = ''
    file_type: str = ''
    files: tuple[GeneratedDocumentFile, ...] = field(default_factory=tuple)
    source_name: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'files', tuple(self.files))

    @property
    def success(self) -> bool:
        return self.status == DOCUMENT_RENDER_STATUS_GENERATED


@dataclass(frozen=True)
class GeneratedFile:
    filename: str
    content: bytes
    content_type: str


@dataclass(frozen=True)
class GeneratedFileResult:
    status: str
    file: Optional[GeneratedFile] = None

    @property
    def success(self) -> bool:
        return self.status == GENERATED_FILE_STATUS_READY
