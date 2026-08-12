"""Entities for planning legacy task classification backfills."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class BackfillContentEntryRef:
    pk: str
    codifier_id: str
    code: str
    topic_id: str = ''
    subtopic_id: str = ''


@dataclass(frozen=True)
class BackfillRequirementRef:
    pk: str
    codifier_id: str
    code: str


@dataclass(frozen=True)
class BackfillTaskRef:
    pk: str
    topic_id: str
    subtopic_id: str = ''
    legacy_content_code: str = ''
    legacy_requirement_code: str = ''
    content_entry_ids: Tuple[str, ...] = ()
    content_codifier_ids: Tuple[str, ...] = ()
    requirement_ids: Tuple[str, ...] = ()
    requirement_codifier_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskClassificationBackfillSnapshot:
    tasks: Tuple[BackfillTaskRef, ...]
    content_entries: Tuple[BackfillContentEntryRef, ...]
    requirements: Tuple[BackfillRequirementRef, ...]


@dataclass(frozen=True)
class TaskClassificationBackfillMutation:
    task_id: str
    relation_type: str
    target_id: str
    reason: str


@dataclass(frozen=True)
class TaskClassificationBackfillIssue:
    task_id: str
    relation_type: str
    code: str
    status: str
    candidate_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskClassificationBackfillPlan:
    mutations: Tuple[TaskClassificationBackfillMutation, ...] = ()
    issues: Tuple[TaskClassificationBackfillIssue, ...] = ()

    @property
    def content_count(self) -> int:
        return sum(item.relation_type == 'content' for item in self.mutations)

    @property
    def requirement_count(self) -> int:
        return sum(
            item.relation_type == 'requirement'
            for item in self.mutations
        )


@dataclass(frozen=True)
class BackfillTaskClassificationsRequest:
    apply: bool = False


@dataclass(frozen=True)
class BackfillTaskClassificationsResult:
    status: str
    plan: TaskClassificationBackfillPlan
