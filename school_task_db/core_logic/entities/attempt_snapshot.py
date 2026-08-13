"""References returned after capturing a checked student attempt."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from core_logic.value_objects.task_content_snapshot import TaskContentSnapshot


@dataclass(frozen=True)
class AttemptSnapshotRef:
    pk: str
    participation_id: str
    mark_id: str
    revision: int


@dataclass(frozen=True)
class CapturedAttemptTaskResult:
    task: TaskContentSnapshot
    order: int
    points: Optional[float]
    max_points: float
    comment: str
    source_selection_id: str
    source_selection_name: str
    content_order: int
    is_assessable: bool


@dataclass(frozen=True)
class CapturedStudentTaskResult:
    student_id: str
    event_id: str
    event_name: str
    event_date: datetime
    captured_at: datetime
    work_id: str
    task: TaskContentSnapshot
    points: float
    max_points: float
    comment: str
