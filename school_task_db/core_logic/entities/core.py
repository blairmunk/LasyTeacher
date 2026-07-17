"""Core app screen DTOs."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DashboardSummaryData:
    tasks_count: int = 0
    works_count: int = 0
    variants_count: int = 0
    orphan_variants_count: int = 0
    students_count: int = 0
    events_count: int = 0
    groups_count: int = 0


@dataclass(frozen=True)
class GlobalSearchData:
    query: str = ''
    results: Dict[str, Any] = None
    total_found: int = 0
    search_mode: Optional[str] = None
    found_text: str = ''

    def __post_init__(self):
        if self.results is None:
            object.__setattr__(self, 'results', {})
