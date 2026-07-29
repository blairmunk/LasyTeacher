"""Normalized access to per-task review scores."""

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Tuple


@dataclass(frozen=True)
class TaskScoreRecord:
    score_key: str
    task_id: str
    variant_task_id: str = ''
    points: Any = None
    max_points: Any = None
    comment: str = ''
    raw: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'score_key', str(self.score_key).strip())
        object.__setattr__(self, 'task_id', str(self.task_id).strip())
        object.__setattr__(
            self,
            'variant_task_id',
            str(self.variant_task_id).strip(),
        )
        object.__setattr__(self, 'comment', str(self.comment or ''))
        object.__setattr__(self, 'raw', dict(self.raw or {}))
        if not self.score_key:
            raise ValueError('score_key is required')
        if not self.task_id:
            raise ValueError('task_id is required')


def normalize_task_scores(task_scores) -> Tuple[TaskScoreRecord, ...]:
    if not isinstance(task_scores, Mapping):
        return ()

    records = []
    for score_key, score_data in task_scores.items():
        if not isinstance(score_data, Mapping):
            continue

        raw = dict(score_data)
        task_id = str(raw.get('task_id') or score_key).strip()
        variant_task_id = str(raw.get('variant_task_id') or '').strip()
        if task_id != str(score_key):
            variant_task_id = variant_task_id or str(score_key)

        try:
            records.append(
                TaskScoreRecord(
                    score_key=str(score_key),
                    task_id=task_id,
                    variant_task_id=variant_task_id,
                    points=raw.get('points'),
                    max_points=raw.get('max_points'),
                    comment=raw.get('comment', ''),
                    raw=raw,
                )
            )
        except ValueError:
            continue

    return tuple(records)


def task_score_records_by_task_id(task_scores) -> dict[str, TaskScoreRecord]:
    return {
        record.task_id: record
        for record in normalize_task_scores(task_scores)
    }


def task_score_records_by_score_key(task_scores) -> dict[str, TaskScoreRecord]:
    return {
        record.score_key: record
        for record in normalize_task_scores(task_scores)
    }


def task_score_records_by_variant_task_id(
    task_scores,
) -> dict[str, TaskScoreRecord]:
    return {
        record.variant_task_id: record
        for record in normalize_task_scores(task_scores)
        if record.variant_task_id
    }


def resolve_task_score_record(
    task_scores,
    *,
    variant_task_id: str = '',
    task_id: str = '',
):
    """Resolve a canonical snapshot score with legacy task-key fallback."""
    variant_task_id = str(variant_task_id or '').strip()
    task_id = str(task_id or '').strip()
    if variant_task_id:
        record = task_score_records_by_variant_task_id(task_scores).get(
            variant_task_id,
        )
        if record:
            return record
        record = task_score_records_by_score_key(task_scores).get(
            variant_task_id,
        )
        if record:
            return replace(
                record,
                task_id=task_id or record.task_id,
                variant_task_id=variant_task_id,
            )
    if task_id:
        return task_score_records_by_task_id(task_scores).get(task_id)
    return None
