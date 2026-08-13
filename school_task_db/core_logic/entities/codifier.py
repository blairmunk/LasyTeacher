"""Codifier screen read models."""

from dataclasses import dataclass, field
from typing import Optional, Tuple


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
    topic: Optional[CodifierObjectRef] = None
    subtopic: Optional[CodifierObjectRef] = None
    grade_studied: str = ''
    task_count: int = 0
    sibling_codes: Tuple[CodifierSiblingCode, ...] = field(default_factory=tuple)
    children: Tuple['CodifierContentEntry', ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CodifierRequirement:
    code: str
    name: str
    cognitive_level: str = ''
    cognitive_level_display: str = ''
    task_count: int = 0


@dataclass(frozen=True)
class CodifierCoverage:
    total: int = 0
    covered: int = 0
    uncovered: int = 0
    pct: int = 0


@dataclass(frozen=True)
class CodifierListData:
    codifiers: Tuple[CodifierListItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CodifierDetailData:
    codifier: Optional[CodifierDetailSpec] = None
    content_tree: Tuple[CodifierContentEntry, ...] = field(default_factory=tuple)
    requirements: Tuple[CodifierRequirement, ...] = field(default_factory=tuple)
    coverage: CodifierCoverage = field(default_factory=CodifierCoverage)
