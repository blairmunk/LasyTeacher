"""Pure remedial-work task selection logic.

This module intentionally has no Django imports. It mirrors the current
RemedialFromEventView selection rules so we can move the view safely later.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from core_logic.entities.student import TaskResult
from core_logic.interfaces.student_repo import IStudentRepository
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import IWorkRepository


@dataclass(frozen=True)
class RemedialConfig:
    max_tasks_per_group: int = 1
    max_total_tasks: int = 10
    weak_threshold_binary: float = 0.0
    weak_threshold_graded: float = 0.5
    fallback_max_difficulty: int = 6


@dataclass(frozen=True)
class RemedialTaskSelection:
    student_id: str
    task_ids: List[str]
    weak_group_ids: Set[str] = field(default_factory=set)
    target_difficulty: int = 3


class RemedialService:
    def __init__(
        self,
        student_repo: IStudentRepository,
        task_repo: ITaskRepository,
        work_repo: IWorkRepository,
        config: Optional[RemedialConfig] = None,
    ):
        self.student_repo = student_repo
        self.task_repo = task_repo
        self.work_repo = work_repo
        self.config = config or RemedialConfig()

    def select_tasks_for_student(
        self,
        student_id: str,
        event_id: str,
        source_work_id: str,
        mark_score: Optional[int] = None,
    ) -> RemedialTaskSelection:
        work_task_ids = self.work_repo.get_variant_task_ids(source_work_id)
        work_group_ids = self.task_repo.get_group_ids_for_tasks(work_task_ids)

        student_variant_task_ids = self.work_repo.get_student_variant_task_ids(
            source_work_id,
            student_id,
            event_id,
        )

        task_results = self.student_repo.get_task_results_for_event(
            student_id,
            event_id,
        )
        weak_task_ids = self.find_weak_tasks(task_results)

        if weak_task_ids:
            weak_group_ids = (
                self.task_repo.get_group_ids_for_tasks(weak_task_ids)
                & work_group_ids
            )
        else:
            weak_group_ids = set(work_group_ids)

        target_difficulty = self.target_difficulty(mark_score)
        candidate_ids: List[str] = []

        for group_id in sorted(weak_group_ids):
            group_task_ids = self.task_repo.get_tasks_in_group(group_id)
            available_ids = group_task_ids - student_variant_task_ids
            if not available_ids:
                continue

            tasks = self.task_repo.get_tasks_by_difficulty(
                available_ids,
                target_difficulty,
            )
            if not tasks:
                tasks = self.task_repo.get_tasks_by_difficulty(
                    available_ids,
                    self.config.fallback_max_difficulty,
                )

            for task in tasks[:self.config.max_tasks_per_group]:
                if task.id not in candidate_ids:
                    candidate_ids.append(task.id)
                if len(candidate_ids) >= self.config.max_total_tasks:
                    break

            if len(candidate_ids) >= self.config.max_total_tasks:
                break

        return RemedialTaskSelection(
            student_id=student_id,
            task_ids=candidate_ids,
            weak_group_ids=weak_group_ids,
            target_difficulty=target_difficulty,
        )

    def find_weak_tasks(self, results: List[TaskResult]) -> Set[str]:
        weak = set()
        for result in results:
            if result.points is None or result.max_points is None:
                continue
            if result.max_points <= 0:
                continue

            if result.max_points <= 2:
                is_weak = result.points <= self.config.weak_threshold_binary
            else:
                is_weak = (
                    result.points / result.max_points
                    < self.config.weak_threshold_graded
                )

            if is_weak:
                weak.add(result.task_id)

        return weak

    @staticmethod
    def target_difficulty(mark_score: Optional[int]) -> int:
        if mark_score is None:
            return 3
        if mark_score <= 2:
            return 3
        if mark_score == 3:
            return 4
        return 6

