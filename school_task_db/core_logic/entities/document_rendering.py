"""Document rendering DTOs."""

from dataclasses import dataclass, field
from typing import List, Optional


DOCUMENT_RENDER_STATUS_GENERATED = 'generated'
DOCUMENT_RENDER_STATUS_NOT_FOUND = 'not_found'
DOCUMENT_RENDER_STATUS_NOT_REMEDIAL = 'not_remedial'
DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER = 'unsupported_renderer'
DOCUMENT_RENDER_STATUS_UNSUPPORTED_GENERATOR = 'unsupported_generator'
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
    files: List[GeneratedDocumentFile] = field(default_factory=list)


@dataclass(frozen=True, init=False)
class DocumentRenderResult:
    status: str
    renderer_type: str
    file_type: str = ''
    files: List[GeneratedDocumentFile] = field(default_factory=list)
    source_name: str = ''

    def __init__(
        self,
        status: str,
        renderer_type: str = '',
        file_type: str = '',
        files: Optional[List[GeneratedDocumentFile]] = None,
        source_name: str = '',
        generator_type: Optional[str] = None,
    ):
        object.__setattr__(self, 'status', status)
        object.__setattr__(self, 'renderer_type', renderer_type or generator_type or '')
        object.__setattr__(self, 'file_type', file_type)
        object.__setattr__(self, 'files', files or [])
        object.__setattr__(self, 'source_name', source_name)

    @property
    def generator_type(self) -> str:
        return self.renderer_type

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


DocumentGenerationResult = DocumentRenderResult
