"""Codifier screen DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class CodifierListData:
    codifiers: Any


@dataclass(frozen=True)
class CodifierListItem:
    pk: str
    short_name: str
    name: str
    exam_type: str
    is_active: bool
    content_entries_count: int = 0
    requirements_count: int = 0


@dataclass(frozen=True)
class CodifierDetailData:
    codifier: Any = None
    content_tree: List["CodifierContentEntry"] = field(default_factory=list)
    requirements: List["CodifierRequirement"] = field(default_factory=list)
    coverage: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class CodifierDetailSpec:
    pk: str
    short_name: str
    name: str
    content_entries_count: int = 0


@dataclass(frozen=True)
class CodifierObjectRef:
    name: str = ''
    short_name: str = ''


@dataclass(frozen=True)
class CodifierSiblingCode:
    codifier: CodifierObjectRef
    code: str


@dataclass(frozen=True)
class CodifierContentEntry:
    code: str
    name: str
    topic: Any = None
    subtopic: Any = None
    grade_studied: str = ''
    task_count: int = 0
    sibling_codes: List[CodifierSiblingCode] = field(default_factory=list)
    children: List["CodifierContentEntry"] = field(default_factory=list)


@dataclass(frozen=True)
class CodifierRequirement:
    code: str
    name: str
    cognitive_level: str = ''
    cognitive_level_display: str = ''
    task_count: int = 0
