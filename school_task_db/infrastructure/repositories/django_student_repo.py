"""Django implementation of the student repository."""

from typing import List

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    StudentGroupRef,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    TaskResult,
    WorkGroupRef,
    WorkRef,
)
from core_logic.interfaces.student_repo import IStudentRepository
from events.models import EventParticipation, Mark
from task_groups.models import TaskGroup
from students.models import StudentGroup, StudentTaskLog
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
