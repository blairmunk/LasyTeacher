"""Document generation DTOs."""

from dataclasses import dataclass, field
from typing import List


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
