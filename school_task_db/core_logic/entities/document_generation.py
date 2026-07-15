"""Document generation DTOs."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class GeneratedDocument:
    file_type: str
    file_paths: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentGenerationResult:
    status: str
    generator_type: str
    file_type: str = ''
    file_paths: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == 'generated'


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
        return self.status == 'ready'
