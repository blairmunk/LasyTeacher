"""Core app screen DTOs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardSummaryData:
    tasks_count: int = 0
    works_count: int = 0
    variants_count: int = 0
    orphan_variants_count: int = 0
    students_count: int = 0
    events_count: int = 0
    groups_count: int = 0
