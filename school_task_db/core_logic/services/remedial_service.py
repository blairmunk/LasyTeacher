"""Pure remedial-work task selection logic.

This module intentionally has no Django imports. It mirrors the current
RemedialFromEventView selection rules so we can move the view safely later.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from core_logic.entities.student import TaskResult
from core_logic.interfaces.student_learning_repo import (
    IStudentLearningRepository,
)
from core_logic.interfaces.remedial_source_repo import (
    IRemedialSourceRepository,
)
from core_logic.interfaces.task_group_repo import ITaskGroupRepository
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.services.student_task_result_service import (
    StudentTaskResultService,
)

REMEDIAL_SOURCE_EVENT_STATUSES = frozenset(('reviewing', 'graded', 'closed'))


@dataclass(frozen=True)
class RemedialConfig:
    max_tasks_per_group: int = 1
    max_total_tasks: int = 10
    weak_threshold_binary: float = 0.0
    weak_threshold_graded: float = 0.5
    fallback_max_difficulty: int = 6


@dataclass(frozen=True)
class RemedialSelectionLimits:
    tasks_per_group: int = 1
    max_total_tasks: int = 10

    def __post_init__(self):
        if self.tasks_per_group < 1:
            raise ValueError('tasks_per_group must be positive')
        if self.max_total_tasks < 1:
            raise ValueError('max_total_tasks must be positive')


@dataclass(frozen=True)
class RemedialTaskSelection:
    student_id: str
    task_ids: List[str]
    weak_group_ids: Set[str] = field(default_factory=set)
    exhausted_group_ids: Set[str] = field(default_factory=set)
    target_difficulty: int = 3
    requested_tasks_count: int = 0

    @property
    def shortage_count(self) -> int:
        return max(0, self.requested_tasks_count - len(self.task_ids))


class RemedialService:
    def __init__(
        self,
        student_learning_repo: IStudentLearningRepository,
        task_repo: ITaskRepository,
        task_group_repo: ITaskGroupRepository,
        remedial_source_repo: IRemedialSourceRepository,
        config: Optional[RemedialConfig] = None,
        task_result_service=None,
    ):
        self.student_learning_repo = student_learning_repo
        self.task_repo = task_repo
        self.task_group_repo = task_group_repo
        self.remedial_source_repo = remedial_source_repo
        self.config = config or RemedialConfig()
        self.task_result_service = (
            task_result_service or StudentTaskResultService()
        )

    def select_tasks_for_student(
        self,
        student_id: str,
        event_id: str,
        mark_score: Optional[int] = None,
        limits: Optional[RemedialSelectionLimits] = None,
    ) -> RemedialTaskSelection:
        limits = limits or RemedialSelectionLimits(
            tasks_per_group=self.config.max_tasks_per_group,
            max_total_tasks=self.config.max_total_tasks,
        )
        event_variant_task_ids = (
            self.remedial_source_repo.get_event_variant_task_ids(
                event_id,
                student_id,
            )
        )
        attempted_task_ids = (
            event_variant_task_ids
            | self._student_attempted_task_ids(student_id)
        )

        task_results = self.task_result_service.build(
            self.student_learning_repo.get_task_results_source_for_event(
                student_id,
                event_id,
            ),
        )
        weak_task_ids = self.find_weak_tasks(task_results)

        if weak_task_ids:
            weak_group_ids = self.task_group_repo.get_group_ids_for_tasks(
                weak_task_ids,
            )
        else:
            weak_group_ids = self.task_group_repo.get_group_ids_for_tasks(
                event_variant_task_ids,
            )

        target_difficulty = self.target_difficulty(mark_score)
        candidate_ids: List[str] = []
        exhausted_group_ids = set()
        requested_tasks_count = min(
            limits.max_total_tasks,
            len(weak_group_ids) * limits.tasks_per_group,
        )

        for group_id in sorted(weak_group_ids):
            group_task_ids = self.task_group_repo.get_tasks_in_group(group_id)
            available_ids = (
                group_task_ids
                - attempted_task_ids
                - set(candidate_ids)
            )
            if not available_ids:
                exhausted_group_ids.add(group_id)
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

            remaining_total = limits.max_total_tasks - len(candidate_ids)
            group_limit = min(limits.tasks_per_group, remaining_total)
            selected_for_group = tasks[:group_limit]
            if len(selected_for_group) < group_limit:
                exhausted_group_ids.add(group_id)

            for task in selected_for_group:
                if task.id not in candidate_ids:
                    candidate_ids.append(task.id)
                if len(candidate_ids) >= limits.max_total_tasks:
                    break

            if len(candidate_ids) >= limits.max_total_tasks:
                break

        return RemedialTaskSelection(
            student_id=student_id,
            task_ids=candidate_ids,
            weak_group_ids=weak_group_ids,
            exhausted_group_ids=exhausted_group_ids,
            target_difficulty=target_difficulty,
            requested_tasks_count=requested_tasks_count,
        )

    def _student_attempted_task_ids(self, student_id: str) -> Set[str]:
        return {
            str(log.task.pk)
            for log in self.student_learning_repo.get_task_logs(student_id)
        }

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
