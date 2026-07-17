"""Codifier screen DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class CodifierListData:
    codifiers: Any


@dataclass(frozen=True)
class CodifierDetailData:
    codifier: Any = None
    content_tree: List[Any] = field(default_factory=list)
    requirements: Any = None
    coverage: Dict[str, int] = field(default_factory=dict)
