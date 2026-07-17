"""Curriculum screen DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class CourseDetailData:
    assignments: List[Any] = field(default_factory=list)
    total_variants: int = 0
    works_by_type: Dict[str, int] = field(default_factory=dict)
    groups_coverage: Dict[str, int] = field(default_factory=dict)
