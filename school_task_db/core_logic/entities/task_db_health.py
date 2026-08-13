"""DTOs for task database diagnostics."""

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from core_logic.entities.report_refs import (
    ReportAnalogGroupRef,
    ReportCourseRef,
    ReportTaskUsageRef,
    ReportVariantRef,
    ReportWorkRef,
)


T = TypeVar('T')


@dataclass(frozen=True)
class TaskDBStats:
    total_tasks: int
    total_groups: int
    total_works: int
    total_variants: int


@dataclass(frozen=True)
class TaskDBIssueCollection(Generic[T]):
    count: int
    items: tuple[T, ...]


@dataclass(frozen=True)
class TaskCoverageIssue:
    work: ReportWorkRef
    group: ReportAnalogGroupRef
    needed: int
    available: int
    deficit: int


@dataclass(frozen=True)
class TaskCountRatio:
    count: int
    pct: float


@dataclass(frozen=True)
class TaskDifficultyDistribution:
    difficulty: int
    count: int
    pct: float


@dataclass(frozen=True)
class TaskTypeDistribution:
    task_type: str
    count: int
    label: str
    pct: float


@dataclass(frozen=True)
class TaskGroupSizeDistribution:
    task_count: int
    group_count: int


@dataclass(frozen=True)
class TaskDBHealthSummary:
    label: str
    color: str
    icon: str
    issues: int
    issues_text: str


@dataclass(frozen=True)
class TaskDBHealthData:
    stats: TaskDBStats
    orphan_variants: TaskDBIssueCollection[ReportVariantRef]
    empty_groups: TaskDBIssueCollection[ReportAnalogGroupRef]
    coverage_issues: TaskDBIssueCollection[TaskCoverageIssue]
    difficulty_dist: tuple[TaskDifficultyDistribution, ...]
    ungrouped_tasks: TaskCountRatio
    fragile_groups: TaskDBIssueCollection[ReportAnalogGroupRef]
    works_no_variants: TaskDBIssueCollection[ReportWorkRef]
    works_no_spec: TaskDBIssueCollection[ReportWorkRef]
    type_dist: tuple[TaskTypeDistribution, ...]
    most_used_tasks: tuple[ReportTaskUsageRef, ...]
    group_sizes: tuple[TaskGroupSizeDistribution, ...]
    unverified_tasks: TaskCountRatio
    no_source_tasks: TaskCountRatio
    no_grade_tasks: TaskCountRatio
    health: TaskDBHealthSummary
    courses: tuple[ReportCourseRef, ...]
    active_report: str = 'db-health'
    active_course_pk: Optional[str] = None


@dataclass(frozen=True)
class TaskGroupSizeFact:
    group: ReportAnalogGroupRef
    task_count: int


@dataclass(frozen=True)
class TaskCoverageFact:
    work: ReportWorkRef
    group: ReportAnalogGroupRef
    needed: int
    available: int


@dataclass(frozen=True)
class TaskDistributionFact:
    key: int | str | None
    count: int
    label: str = ''


@dataclass(frozen=True)
class TaskDBHealthSource:
    total_tasks: int
    total_works: int
    total_variants: int
    orphan_variants_count: int
    orphan_variant_samples: tuple[ReportVariantRef, ...]
    group_sizes: tuple[TaskGroupSizeFact, ...]
    coverage: tuple[TaskCoverageFact, ...]
    ungrouped_tasks_count: int
    works_no_variants_count: int
    works_no_variant_samples: tuple[ReportWorkRef, ...]
    works_no_spec_count: int
    works_no_spec_samples: tuple[ReportWorkRef, ...]
    difficulty_counts: tuple[TaskDistributionFact, ...]
    type_counts: tuple[TaskDistributionFact, ...]
    most_used_tasks: tuple[ReportTaskUsageRef, ...]
    unverified_tasks_count: int
    no_source_tasks_count: int
    no_grade_tasks_count: int
    courses: tuple[ReportCourseRef, ...]
