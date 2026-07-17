"""Django implementation of the student repository."""

import random
from typing import List

from django.db.models import Avg, Count, Q

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    RemedialWizardPreviewData,
    StudentDetail,
    StudentGroupDetail,
    StudentGroupDetailStudent,
    StudentGroupListItem,
    StudentGroupRef,
    StudentListItem,
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
    def _student_detail(self, student):
        return StudentDetail(
            pk=str(student.pk),
            first_name=student.first_name,
            last_name=student.last_name,
            middle_name=student.middle_name,
            email=student.email,
            short_uuid=student.get_short_uuid(),
            full_name=student.get_full_name(),
            short_name=student.get_short_name(),
        )

    def get_list_students(self):
        return [
            StudentListItem(
                pk=str(student.pk),
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
                email=student.email,
                created_at=student.created_at,
            )
            for student in Student.objects.all().order_by(
                'last_name',
                'first_name',
            )
        ]

    def get_list_student_groups(self):
        return [
            StudentGroupListItem(
                pk=str(group.pk),
                name=group.name,
                short_uuid=group.get_short_uuid(),
                created_at=group.created_at,
                students_count=group.students_count,
            )
            for group in StudentGroup.objects.select_related(
                'academic_year',
            ).annotate(
                students_count=Count('students'),
            ).order_by('name')
        ]

    def get_student(self, student_id: str):
        student = Student.objects.filter(pk=student_id).first()
        if student is None:
            return None

        return self._student_detail(student)

    def get_student_group(self, group_id: str):
        group = StudentGroup.objects.select_related(
            'academic_year',
        ).prefetch_related(
            'students',
        ).filter(pk=group_id).first()
        if group is None:
            return None

        return StudentGroupDetail(
            pk=str(group.pk),
            name=group.name,
            short_uuid=group.get_short_uuid(),
            created_at=group.created_at,
            students=[
                StudentGroupDetailStudent(
                    pk=str(student.pk),
                    last_name=student.last_name,
                    first_name=student.first_name,
                    middle_name=student.middle_name,
                    email=student.email,
                    short_uuid=student.get_short_uuid(),
                )
                for student in group.students.all().order_by(
                    'last_name',
                    'first_name',
                )
            ],
        )

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

    def get_all_student_groups(self) -> List[StudentGroupRef]:
        return [
            StudentGroupRef(pk=str(group.pk), name=str(group))
            for group in StudentGroup.objects.select_related(
                'academic_year',
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

    def get_group_name(self, group_id: str):
        group = StudentGroup.objects.filter(pk=group_id).first()
        return group.name if group else None

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

    def get_remedial_wizard_preview_data(
        self,
        group_id: str,
        threshold: int,
        limit_type: str,
        limit_value: int,
        work_name: str,
    ) -> RemedialWizardPreviewData:
        group = StudentGroup.objects.filter(pk=group_id).first()
        if not group:
            return RemedialWizardPreviewData(status='not_found')

        preview = []
        for student in group.get_active_students():
            task_logs = StudentTaskLog.objects.filter(student=student)
            if not task_logs.exists():
                preview.append({
                    'student': self._student_detail(student),
                    'student_level': 'unknown',
                    'student_level_label': '—',
                    'overall_avg': 0,
                    'weak_groups': 0,
                    'tasks_count': 0,
                    'total_weight': 0,
                    'est_time': 0,
                    'available': False,
                    'reason': 'Нет данных',
                })
                continue

            done_task_ids = set(task_logs.values_list('task_id', flat=True))
            overall_avg = task_logs.aggregate(avg=Avg('percentage'))['avg'] or 0

            if overall_avg < 50:
                student_level = 'weak'
            elif overall_avg < 80:
                student_level = 'medium'
            else:
                student_level = 'strong'

            weak_group_ids = list(
                task_logs.exclude(
                    analog_group__isnull=True,
                ).values(
                    'analog_group',
                ).annotate(
                    avg_pct=Avg('percentage'),
                ).filter(
                    avg_pct__lt=threshold,
                ).values_list('analog_group', flat=True)
            )

            all_group_ids = list(
                task_logs.exclude(
                    analog_group__isnull=True,
                ).values_list(
                    'analog_group',
                    flat=True,
                ).distinct()
            )

            candidate_tasks = self._wizard_candidate_tasks(
                student_level=student_level,
                weak_group_ids=weak_group_ids,
                all_group_ids=all_group_ids,
                done_task_ids=done_task_ids,
            )
            selected = self._wizard_selected_tasks(
                candidate_tasks=candidate_tasks,
                limit_type=limit_type,
                limit_value=limit_value,
            )
            total_weight = sum(task['difficulty'] for task in selected)
            est_time = sum(
                task['estimated_time'] or task['difficulty'] * 3
                for task in selected
            )
            level_labels = {
                'weak': 'Слабый',
                'medium': 'Средний',
                'strong': 'Сильный',
            }

            preview.append({
                'student': self._student_detail(student),
                'student_level': student_level,
                'student_level_label': level_labels[student_level],
                'overall_avg': round(overall_avg, 1),
                'weak_groups': len(weak_group_ids),
                'tasks_count': len(selected),
                'total_weight': total_weight,
                'est_time': est_time,
                'available': len(selected) > 0,
                'reason': (
                    ''
                    if selected
                    else 'Нет слабых групп или все задания решены'
                ),
                'task_ids': [task['id'] for task in selected],
            })

        return RemedialWizardPreviewData(
            group=group,
            preview=preview,
            threshold=threshold,
            limit_type=limit_type,
            limit_value=limit_value,
            work_name=work_name,
            students_with_tasks=sum(1 for row in preview if row['available']),
            total_tasks=sum(row['tasks_count'] for row in preview),
        )

    def _wizard_candidate_tasks(
        self,
        student_level,
        weak_group_ids,
        all_group_ids,
        done_task_ids,
    ):
        candidate_tasks = []

        if student_level == 'weak':
            for group_id in weak_group_ids:
                group_diff = self._group_effective_difficulty(group_id)
                candidate_tasks.extend(
                    self._tasks_for_group(
                        group_id=group_id,
                        done_task_ids=done_task_ids,
                        difficulty_filter={'difficulty__lte': group_diff},
                    )
                )
        elif student_level == 'medium':
            for group_id in weak_group_ids:
                group_diff = self._group_effective_difficulty(group_id)
                found = self._tasks_for_group(
                    group_id=group_id,
                    done_task_ids=done_task_ids,
                    difficulty_filter={'difficulty': group_diff},
                )
                if not found:
                    found = self._tasks_for_group(
                        group_id=group_id,
                        done_task_ids=done_task_ids,
                        difficulty_filter={
                            'difficulty__gte': max(1, group_diff - 1),
                            'difficulty__lte': group_diff + 1,
                        },
                    )
                candidate_tasks.extend(found)
        else:
            for group_id in all_group_ids:
                group_diff = self._group_effective_difficulty(group_id)
                candidate_tasks.extend(
                    self._tasks_for_group(
                        group_id=group_id,
                        done_task_ids=done_task_ids,
                        difficulty_filter={'difficulty__gt': group_diff},
                    )
                )

            if not candidate_tasks:
                all_group_task_ids = set(
                    TaskGroup.objects.filter(
                        group_id__in=all_group_ids,
                    ).values_list(
                        'task_id',
                        flat=True,
                    )
                )
                tasks = Task.objects.filter(
                    id__in=all_group_task_ids - done_task_ids,
                    difficulty__gte=4,
                ).values('id', 'difficulty', 'estimated_time')
                candidate_tasks.extend(
                    self._wizard_task_rows(tasks, group_id=None)
                )

        return candidate_tasks

    def _tasks_for_group(self, group_id, done_task_ids, difficulty_filter):
        group_task_ids = set(
            TaskGroup.objects.filter(group_id=group_id).values_list(
                'task_id',
                flat=True,
            )
        )
        available_ids = group_task_ids - done_task_ids
        if not available_ids:
            return []

        tasks = Task.objects.filter(
            id__in=available_ids,
            **difficulty_filter,
        ).values('id', 'difficulty', 'estimated_time')
        return self._wizard_task_rows(tasks, group_id=group_id)

    def _wizard_task_rows(self, tasks, group_id):
        return [
            {
                'id': task['id'],
                'difficulty': task['difficulty'] or 1,
                'estimated_time': task['estimated_time'] or 0,
                'group_id': group_id,
            }
            for task in tasks
        ]

    def _group_effective_difficulty(self, group_id):
        try:
            return AnalogGroup.objects.get(pk=group_id).effective_difficulty
        except AnalogGroup.DoesNotExist:
            return 3

    def _wizard_selected_tasks(self, candidate_tasks, limit_type, limit_value):
        random.shuffle(candidate_tasks)
        selected = []
        running_total = 0

        for candidate_task in candidate_tasks:
            if limit_type == 'tasks' and len(selected) >= limit_value:
                break
            if limit_type == 'weight' and running_total >= limit_value:
                break
            if limit_type == 'time' and running_total >= limit_value:
                break

            selected.append(candidate_task)
            if limit_type == 'tasks':
                running_total = len(selected)
            elif limit_type == 'weight':
                running_total += candidate_task['difficulty']
            elif limit_type == 'time':
                running_total += (
                    candidate_task['estimated_time']
                    or candidate_task['difficulty'] * 3
                )

        return selected

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
