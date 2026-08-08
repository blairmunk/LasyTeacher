"""DTOs for task database diagnostics."""

from dataclasses import dataclass
from typing import Any, List

from core_logic.entities.report import (
    ReportAnalogGroupRef,
    ReportCourseRef,
    ReportTaskUsageRef,
    ReportVariantRef,
    ReportWorkRef,
)


@dataclass(frozen=True)
class TaskDBHealthData:
    stats: dict
    orphan_variants: dict
    empty_groups: dict
    coverage_issues: dict
    difficulty_dist: List[dict]
    ungrouped_tasks: dict
    fragile_groups: dict
    works_no_variants: dict
    works_no_spec: dict
    type_dist: List[dict]
    most_used_tasks: Any
    group_sizes: List[dict]
    unverified_tasks: dict
    no_source_tasks: dict
    no_grade_tasks: dict
    health: dict
    courses: Any
    active_report: str = 'db-health'
    active_course_pk: Any = None


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
    key: Any
    count: int
    label: str = ''


@dataclass(frozen=True)
class TaskDBHealthSource:
    total_tasks: int
    total_works: int
    total_variants: int
    orphan_variants_count: int
    orphan_variant_samples: List[ReportVariantRef]
    group_sizes: List[TaskGroupSizeFact]
    coverage: List[TaskCoverageFact]
    ungrouped_tasks_count: int
    works_no_variants_count: int
    works_no_variant_samples: List[ReportWorkRef]
    works_no_spec_count: int
    works_no_spec_samples: List[ReportWorkRef]
    difficulty_counts: List[TaskDistributionFact]
    type_counts: List[TaskDistributionFact]
    most_used_tasks: List[ReportTaskUsageRef]
    unverified_tasks_count: int
    no_source_tasks_count: int
    no_grade_tasks_count: int
    courses: List[ReportCourseRef]
