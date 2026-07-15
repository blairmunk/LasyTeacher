"""Django implementation of the student repository."""

import random
from typing import List

from django.db.models import Avg, Count, Q

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    StudentGroupRef,
    StudentParticipationProfile,
    StudentRemedialWorkData,
    StudentTaskLogProfile,
    TaskResult,
    WorkGroupRef,
    WorkRef,
)
from core_logic.interfaces.student_repo import IStudentRepository
from events.models import EventParticipation, Mark
from task_groups.models import AnalogGroup, TaskGroup
from students.models import StudentGroup, StudentTaskLog
from students.models import Student
from tasks.models import Task
from works.models import WorkAnalogGroup


class DjangoStudentRepository(IStudentRepository):
    def get_task_results_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> List[TaskResult]:
        participation = EventParticipation.objects.filter(
            student_id=student_id,
            event_id=event_id,
        ).first()
        if not participation:
            return []

        mark = Mark.objects.filter(participation=participation).first()
        if not mark or not mark.task_scores:
            return []

        results = []
        task_groups = {
            str(tg.task_id): tg
            for tg in TaskGroup.objects.filter(
                task_id__in=mark.task_scores.keys()
            ).select_related('group')
        }

        for task_id, score_data in mark.task_scores.items():
            if not isinstance(score_data, dict):
                continue

            task_group = task_groups.get(str(task_id))
            results.append(
                TaskResult(
                    task_id=str(task_id),
                    points=score_data.get('points'),
                    max_points=score_data.get('max_points'),
                    group_id=str(task_group.group_id) if task_group else None,
                    group_name=task_group.group.name if task_group else '',
                )
            )

        return results

    def get_student_groups(self, student_id: str) -> List[StudentGroupRef]:
        return [
            StudentGroupRef(pk=str(group.pk), name=group.name)
            for group in StudentGroup.objects.filter(
                students__id=student_id,
            ).order_by('name')
        ]

    def get_profile_participations(
        self,
        student_id: str,
    ) -> List[StudentParticipationProfile]:
        participations = EventParticipation.objects.filter(
            student_id=student_id,
        ).select_related(
            'event',
            'event__work',
            'variant',
        ).order_by('-event__planned_date')

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation__student_id=student_id,
            )
        }

        rows = []
        for participation in participations:
            event = participation.event
            work = event.work if event else None
            mark = marks.get(participation.pk)
            rows.append(
                StudentParticipationProfile(
                    participation=ObjectRef(
                        pk=str(participation.pk),
                        name=str(participation),
                    ),
                    event=EventRef(
                        pk=str(event.pk),
                        name=event.name,
                        planned_date=event.planned_date,
                    ),
                    work=(
                        WorkRef(
                            pk=str(work.pk),
                            name=work.name,
                            work_type=work.work_type,
                            work_type_display=work.get_work_type_display(),
                        )
                        if work
                        else None
                    ),
                    mark=(
                        MarkRef(
                            pk=str(mark.pk),
                            score=mark.score,
                            points=mark.points,
                            max_points=mark.max_points,
                            teacher_comment=mark.teacher_comment,
                        )
                        if mark
                        else None
                    ),
                    score=mark.score if mark else None,
                    is_absent=participation.status == 'absent',
                    variant_number=participation.variant.number if participation.variant else None,
                )
            )

        return rows

    def get_task_logs(self, student_id: str) -> List[StudentTaskLogProfile]:
        logs = StudentTaskLog.objects.filter(
            student_id=student_id,
        ).select_related(
            'task',
            'event',
            'topic',
            'analog_group',
        ).order_by('-completed_at')

        return [
            StudentTaskLogProfile(
                task=ObjectRef(pk=str(log.task.pk), name=log.task.text),
                event=(
                    ObjectRef(pk=str(log.event.pk), name=log.event.name)
                    if log.event
                    else None
                ),
                topic_name=log.topic.name if log.topic else '',
                analog_group=(
                    ObjectRef(
                        pk=str(log.analog_group.pk),
                        name=log.analog_group.name,
                    )
                    if log.analog_group
                    else None
                ),
                difficulty=log.difficulty,
                points=log.points,
                max_points=log.max_points,
                is_correct=log.is_correct,
                percentage=log.percentage,
                completed_at=log.completed_at,
            )
            for log in logs
        ]

    def get_student_remedial_work_data(
        self,
        student_id: str,
    ) -> StudentRemedialWorkData:
        task_logs = StudentTaskLog.objects.filter(student_id=student_id)
        if not task_logs.exists():
            return StudentRemedialWorkData(no_data=True)

        weak_groups = task_logs.exclude(
            analog_group__isnull=True,
        ).values(
            'analog_group',
            'analog_group__name',
        ).annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            wrong=Count('id', filter=Q(is_correct=False)),
            avg_pct=Avg('percentage'),
        ).filter(
            avg_pct__lt=70,
        ).order_by('avg_pct')

        done_task_ids = set(task_logs.values_list('task_id', flat=True))
        remedial_groups = []
        total_available = 0

        for weak_group in weak_groups:
            group_id = weak_group['analog_group']
            group = AnalogGroup.objects.get(pk=group_id)
            group_task_ids = set(
                TaskGroup.objects.filter(group=group).values_list(
                    'task_id',
                    flat=True,
                )
            )
            available_ids = group_task_ids - done_task_ids
            available_tasks = Task.objects.filter(id__in=available_ids)

            remedial_groups.append({
                'group': group,
                'avg_pct': round(weak_group['avg_pct'] or 0, 1),
                'total_done': weak_group['total'],
                'correct': weak_group['correct'],
                'wrong': weak_group['wrong'],
                'available_count': len(available_ids),
                'available_tasks': available_tasks[:5],
                'group_total': len(group_task_ids),
            })
            total_available += len(available_ids)

        weak_topics = task_logs.exclude(
            topic__isnull=True,
        ).values(
            'topic',
            'topic__name',
        ).annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            avg_pct=Avg('percentage'),
        ).filter(
            avg_pct__lt=70,
        ).order_by('avg_pct')[:10]

        return StudentRemedialWorkData(
            remedial_groups=remedial_groups,
            weak_topics=weak_topics,
            total_available=total_available,
            done_count=len(done_task_ids),
        )

    def get_student_short_name(self, student_id: str) -> str:
        return Student.objects.get(pk=student_id).get_short_name()

    def select_student_remedial_task_ids(
        self,
        student_id: str,
        max_tasks: int,
        selected_group_ids: List[str],
    ) -> List[str]:
        task_logs = StudentTaskLog.objects.filter(student_id=student_id)
        done_task_ids = set(task_logs.values_list('task_id', flat=True))
        tasks_to_add = []

        if selected_group_ids:
            group_ids = selected_group_ids
        else:
            group_ids = task_logs.exclude(
                analog_group__isnull=True,
            ).values(
                'analog_group',
            ).annotate(
                avg_pct=Avg('percentage'),
            ).filter(
                avg_pct__lt=70,
            ).values_list('analog_group', flat=True)

        for group_id in group_ids:
            if len(tasks_to_add) >= max_tasks:
                break

            group_task_ids = set(
                TaskGroup.objects.filter(group_id=group_id).values_list(
                    'task_id',
                    flat=True,
                )
            )
            available_ids = list(group_task_ids - done_task_ids)

            if available_ids:
                random.shuffle(available_ids)
                take = min(2, max_tasks - len(tasks_to_add), len(available_ids))
                tasks_to_add.extend(str(task_id) for task_id in available_ids[:take])

        return tasks_to_add

    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        if not work_ids:
            return []

        return [
            WorkGroupRef(
                work_id=str(work_group.work_id),
                group_id=str(work_group.analog_group_id),
                group_name=work_group.analog_group.name,
            )
            for work_group in WorkAnalogGroup.objects.filter(
                work_id__in=work_ids,
            ).select_related('analog_group')
        ]
