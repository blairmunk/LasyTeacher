"""Pure preview rules for the class remedial-work wizard."""

import random
from collections import defaultdict

from core_logic.entities.student import (
    RemedialWizardPreviewData,
    RemedialWizardPreviewItem,
    RemedialWizardPreviewSource,
)
from core_logic.value_objects.analog_group_difficulty import (
    resolve_analog_group_difficulty,
)


class RemedialWizardService:
    def __init__(self, shuffle=None):
        self.shuffle = shuffle or random.shuffle

    def build(
        self,
        source: RemedialWizardPreviewSource | None,
        *,
        threshold: int,
        limit_type: str,
        limit_value: int,
        work_name: str,
    ) -> RemedialWizardPreviewData:
        if source is None:
            return RemedialWizardPreviewData(status='not_found')

        logs_by_student = defaultdict(list)
        for task_log in source.task_logs:
            logs_by_student[task_log.student_id].append(task_log)

        groups = {
            group.group_id: group
            for group in source.analog_groups
        }
        tasks_by_group = defaultdict(list)
        for task in source.tasks:
            for group_id in task.analog_group_ids:
                tasks_by_group[group_id].append(task)

        preview = []
        for student in source.students:
            task_logs = logs_by_student[student.pk]
            if not task_logs:
                preview.append(self._no_data_row(student))
                continue

            percentages = [
                task_log.percentage
                for task_log in task_logs
                if task_log.percentage is not None
            ]
            overall_avg = (
                sum(percentages) / len(percentages)
                if percentages
                else 0
            )
            student_level = self._student_level(overall_avg)
            done_task_ids = {task_log.task_id for task_log in task_logs}
            group_percentages = defaultdict(list)
            all_group_ids = []
            for task_log in task_logs:
                if not task_log.analog_group_id:
                    continue
                if task_log.analog_group_id not in all_group_ids:
                    all_group_ids.append(task_log.analog_group_id)
                if task_log.percentage is not None:
                    group_percentages[task_log.analog_group_id].append(
                        task_log.percentage
                    )

            weak_group_ids = [
                group_id
                for group_id, values in group_percentages.items()
                if sum(values) / len(values) < threshold
            ]
            candidates = self._candidate_tasks(
                student_level=student_level,
                weak_group_ids=weak_group_ids,
                all_group_ids=all_group_ids,
                done_task_ids=done_task_ids,
                groups=groups,
                tasks_by_group=tasks_by_group,
            )
            selected = self._selected_tasks(
                candidates,
                limit_type=limit_type,
                limit_value=limit_value,
            )
            preview.append(
                RemedialWizardPreviewItem(
                    student=student,
                    student_level=student_level,
                    overall_avg=round(overall_avg, 1),
                    weak_groups=len(weak_group_ids),
                    tasks_count=len(selected),
                    total_weight=sum(task.difficulty for task in selected),
                    est_time=sum(self._task_time(task) for task in selected),
                    available=bool(selected),
                    reason=(
                        ''
                        if selected
                        else 'Нет слабых групп или все задания решены'
                    ),
                    task_ids=tuple(task.task_id for task in selected),
                )
            )

        return RemedialWizardPreviewData(
            group=source.group,
            preview=tuple(preview),
            threshold=threshold,
            limit_type=limit_type,
            limit_value=limit_value,
            work_name=work_name,
            students_with_tasks=sum(1 for row in preview if row.available),
            total_tasks=sum(row.tasks_count for row in preview),
        )

    @staticmethod
    def _no_data_row(student):
        return RemedialWizardPreviewItem(
            student=student,
            student_level='unknown',
            overall_avg=0,
            weak_groups=0,
            tasks_count=0,
            total_weight=0,
            est_time=0,
            available=False,
            reason='Нет данных',
        )

    @staticmethod
    def _student_level(overall_avg):
        if overall_avg < 50:
            return 'weak'
        if overall_avg < 80:
            return 'medium'
        return 'strong'

    def _candidate_tasks(
        self,
        *,
        student_level,
        weak_group_ids,
        all_group_ids,
        done_task_ids,
        groups,
        tasks_by_group,
    ):
        candidates = []
        if student_level == 'weak':
            for group_id in weak_group_ids:
                difficulty = self._effective_difficulty(
                    group_id,
                    groups,
                    tasks_by_group,
                )
                candidates.extend(
                    task
                    for task in tasks_by_group[group_id]
                    if task.task_id not in done_task_ids
                    and task.difficulty <= difficulty
                )
        elif student_level == 'medium':
            for group_id in weak_group_ids:
                difficulty = self._effective_difficulty(
                    group_id,
                    groups,
                    tasks_by_group,
                )
                found = [
                    task
                    for task in tasks_by_group[group_id]
                    if task.task_id not in done_task_ids
                    and task.difficulty == difficulty
                ]
                if not found:
                    found = [
                        task
                        for task in tasks_by_group[group_id]
                        if task.task_id not in done_task_ids
                        and max(1, difficulty - 1)
                        <= task.difficulty
                        <= difficulty + 1
                    ]
                candidates.extend(found)
        else:
            for group_id in all_group_ids:
                difficulty = self._effective_difficulty(
                    group_id,
                    groups,
                    tasks_by_group,
                )
                candidates.extend(
                    task
                    for task in tasks_by_group[group_id]
                    if task.task_id not in done_task_ids
                    and task.difficulty > difficulty
                )
            if not candidates:
                candidates.extend(
                    task
                    for task in self._unique_tasks(all_group_ids, tasks_by_group)
                    if task.task_id not in done_task_ids
                    and task.difficulty >= 4
                )
        return candidates

    @staticmethod
    def _effective_difficulty(group_id, groups, tasks_by_group):
        group = groups.get(group_id)
        return resolve_analog_group_difficulty(
            nominal_difficulty=(group.nominal_difficulty if group else 0),
            task_difficulties=(
                task.difficulty
                for task in tasks_by_group[group_id]
            ),
        )

    @staticmethod
    def _unique_tasks(group_ids, tasks_by_group):
        tasks = {}
        for group_id in group_ids:
            for task in tasks_by_group[group_id]:
                tasks.setdefault(task.task_id, task)
        return list(tasks.values())

    def _selected_tasks(self, candidates, *, limit_type, limit_value):
        candidates = list(candidates)
        self.shuffle(candidates)
        selected = []
        running_total = 0
        for task in candidates:
            if limit_type == 'tasks' and len(selected) >= limit_value:
                break
            if limit_type in {'weight', 'time'} and running_total >= limit_value:
                break

            selected.append(task)
            if limit_type == 'tasks':
                running_total = len(selected)
            elif limit_type == 'weight':
                running_total += task.difficulty
            elif limit_type == 'time':
                running_total += self._task_time(task)
        return selected

    @staticmethod
    def _task_time(task):
        return task.estimated_time or task.difficulty * 3
