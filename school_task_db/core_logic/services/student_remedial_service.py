"""Pure analysis and task selection for one student's remedial work."""

import random
from collections import defaultdict
from typing import Sequence

from core_logic.entities.student import (
    ObjectRef,
    StudentRemedialGroup,
    StudentRemedialSource,
    StudentWeakTopic,
    StudentRemedialWorkData,
)


class StudentRemedialService:
    def __init__(self, shuffle=None):
        self.shuffle = shuffle or random.shuffle

    def analyze(self, source: StudentRemedialSource) -> StudentRemedialWorkData:
        if not source.task_logs:
            return StudentRemedialWorkData(no_data=True)

        done_task_ids = {task_log.task_id for task_log in source.task_logs}
        tasks_by_group = self._tasks_by_group(source)
        group_logs = defaultdict(list)
        topic_logs = defaultdict(list)
        group_refs = {}
        topic_refs = {}
        for task_log in source.task_logs:
            if task_log.analog_group:
                group_id = task_log.analog_group.pk
                group_refs[group_id] = task_log.analog_group
                group_logs[group_id].append(task_log)
            if task_log.topic:
                topic_id = task_log.topic.pk
                topic_refs[topic_id] = task_log.topic
                topic_logs[topic_id].append(task_log)

        remedial_groups = []
        for group_id, logs in group_logs.items():
            avg_pct = self._average_percentage(logs)
            if avg_pct is None or avg_pct >= 70:
                continue
            group_tasks = tasks_by_group[group_id]
            available_tasks = [
                task
                for task in group_tasks
                if task.task_id not in done_task_ids
            ]
            remedial_groups.append(
                StudentRemedialGroup(
                    group=group_refs[group_id],
                    avg_pct=round(avg_pct, 1),
                    total_done=len(logs),
                    correct=sum(log.is_correct is True for log in logs),
                    wrong=sum(log.is_correct is False for log in logs),
                    available_count=len(available_tasks),
                    available_tasks=tuple(
                        ObjectRef(pk=task.task_id, name=task.text)
                        for task in available_tasks[:5]
                    ),
                    group_total=len(group_tasks),
                )
            )
        remedial_groups.sort(key=lambda row: row.avg_pct)
        total_available = sum(
            row.available_count
            for row in remedial_groups
        )

        weak_topics = []
        for topic_id, logs in topic_logs.items():
            avg_pct = self._average_percentage(logs)
            if avg_pct is None or avg_pct >= 70:
                continue
            weak_topics.append(
                StudentWeakTopic(
                    topic=topic_refs[topic_id],
                    total=len(logs),
                    correct=sum(log.is_correct is True for log in logs),
                    avg_pct=avg_pct,
                )
            )
        weak_topics.sort(key=lambda row: row.avg_pct)

        return StudentRemedialWorkData(
            remedial_groups=tuple(remedial_groups),
            weak_topics=tuple(weak_topics[:10]),
            total_available=total_available,
            done_count=len(done_task_ids),
        )

    def select_task_ids(
        self,
        source: StudentRemedialSource,
        *,
        max_tasks: int,
        selected_group_ids: Sequence[str],
    ) -> tuple[str, ...]:
        done_task_ids = {task_log.task_id for task_log in source.task_logs}
        tasks_by_group = self._tasks_by_group(source)
        group_ids = selected_group_ids or self._weak_group_ids(source)
        selected = []
        for group_id in group_ids:
            if len(selected) >= max_tasks:
                break
            available_ids = [
                task.task_id
                for task in tasks_by_group[group_id]
                if task.task_id not in done_task_ids
                and task.task_id not in selected
            ]
            self.shuffle(available_ids)
            take = min(2, max_tasks - len(selected), len(available_ids))
            selected.extend(available_ids[:take])
        return tuple(selected)

    @staticmethod
    def _tasks_by_group(source):
        tasks_by_group = defaultdict(list)
        for task in source.tasks:
            for group_id in task.analog_group_ids:
                tasks_by_group[group_id].append(task)
        return tasks_by_group

    def _weak_group_ids(self, source):
        logs_by_group = defaultdict(list)
        for task_log in source.task_logs:
            if task_log.analog_group:
                logs_by_group[task_log.analog_group.pk].append(task_log)
        weak_group_ids = []
        for group_id, logs in logs_by_group.items():
            average = self._average_percentage(logs)
            if average is not None and average < 70:
                weak_group_ids.append(group_id)
        return weak_group_ids

    @staticmethod
    def _average_percentage(logs):
        values = [
            task_log.percentage
            for task_log in logs
            if task_log.percentage is not None
        ]
        if not values:
            return None
        return sum(values) / len(values)
