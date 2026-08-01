"""Allocate task scores across work specification rows."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class WorkScoreSpecRow:
    spec_row_id: str
    count: int
    weight: int
    is_assessable: bool = True

    def __post_init__(self):
        if not self.spec_row_id:
            raise ValueError('spec_row_id is required')
        if self.count < 1:
            raise ValueError('count must be positive')
        if self.weight < 0:
            raise ValueError('weight must be non-negative')


@dataclass(frozen=True)
class TaskScoreAllocation:
    spec_row_id: str
    points: int


class WorkScoreAllocationService:
    @staticmethod
    def effective_max_score(max_score: int, spec_rows) -> int:
        if max_score > 0:
            return max_score
        return sum(
            row.weight * row.count
            for row in spec_rows
            if row.is_assessable
        )

    def allocate(
        self,
        max_score: int,
        spec_rows,
    ) -> Tuple[TaskScoreAllocation, ...]:
        slots = tuple(
            (
                row.spec_row_id,
                row.weight if row.is_assessable else 0,
            )
            for row in spec_rows
            for _ in range(row.count)
        )
        if not slots:
            return ()

        if max_score <= 0:
            return tuple(
                TaskScoreAllocation(spec_row_id=row_id, points=weight)
                for row_id, weight in slots
            )

        total_weight = sum(weight for _, weight in slots)
        if total_weight <= 0:
            return tuple(
                TaskScoreAllocation(spec_row_id=row_id, points=0)
                for row_id, _ in slots
            )

        raw_points = [
            weight / total_weight * max_score
            for _, weight in slots
        ]
        allocated_points = [int(points) for points in raw_points]
        remainder = max_score - sum(allocated_points)
        remainder_order = sorted(
            range(len(raw_points)),
            key=lambda index: raw_points[index] - allocated_points[index],
            reverse=True,
        )
        for index in remainder_order[:remainder]:
            allocated_points[index] += 1

        return tuple(
            TaskScoreAllocation(
                spec_row_id=slots[index][0],
                points=allocated_points[index],
            )
            for index in range(len(slots))
        )
