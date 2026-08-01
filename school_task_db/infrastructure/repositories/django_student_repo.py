"""Django implementation of the student repository."""

from collections import defaultdict
from typing import List

from django.db.models import Count, Q

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    RemedialWizardAnalogGroup,
    RemedialWizardPreviewSource,
    RemedialWizardTask,
    RemedialWizardTaskLog,
    SaveStudentGroupParams,
    SaveStudentGroupResult,
    SaveStudentParams,
    SaveStudentResult,
    StudentRemedialCandidateTask,
    StudentRemedialSource,
    StudentRemedialTaskLog,
    StudentDetail,
    StudentGroupDetail,
    StudentGroupDetailStudent,
    StudentGroupListItem,
    StudentGroupRef,
    StudentListItem,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    TaskResultGroupRef,
    TaskResultsSource,
    TaskResultVariantRow,
    TaskLogSyncPlan,
    TaskLogSyncSource,
    TaskLogSyncTask,
    TaskLogSyncVariantTask,
    WorkGroupRef,
    WorkRef,
)
from core_logic.interfaces.student_repo import IStudentRepository
from events.models import EventParticipation, Mark
from task_groups.models import AnalogGroup, TaskGroup
from students.models import StudentGroup, StudentTaskLog
from students.models import Student
from tasks.models import Task
from works.models import VariantTask, WorkAnalogGroup


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

    def get_list_students(self, year=None):
        students = Student.objects.all()
        if year:
            students = students.filter(
                studentgroup__academic_year_id=year.pk,
            ).distinct()
        return [
            StudentListItem(
                pk=str(student.pk),
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
                email=student.email,
                created_at=student.created_at,
            )
            for student in students.order_by(
                'last_name',
                'first_name',
            )
        ]

    def get_list_student_groups(self, year=None):
        groups = StudentGroup.objects.select_related(
            'academic_year',
        )
        if year:
            groups = groups.filter(academic_year_id=year.pk)
        return [
            StudentGroupListItem(
                pk=str(group.pk),
                name=group.name,
                short_uuid=group.get_short_uuid(),
                created_at=group.created_at,
                students_count=group.students_count,
            )
            for group in groups.annotate(
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

    def create_student(self, params: SaveStudentParams) -> SaveStudentResult:
        student = Student.objects.create(
            first_name=params.first_name,
            last_name=params.last_name,
            middle_name=params.middle_name,
            email=params.email,
        )
        return SaveStudentResult(status='created', student_id=str(student.pk))

    def update_student(self, params: SaveStudentParams) -> SaveStudentResult:
        student = Student.objects.filter(pk=params.student_id).first()
        if student is None:
            return SaveStudentResult(status='not_found')

        student.first_name = params.first_name
        student.last_name = params.last_name
        student.middle_name = params.middle_name
        student.email = params.email
        student.save()
        return SaveStudentResult(status='updated', student_id=str(student.pk))

    def create_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        group = StudentGroup.objects.create(name=params.name)
        group.students.set(params.student_ids)
        return SaveStudentGroupResult(status='created', group_id=str(group.pk))

    def update_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        group = StudentGroup.objects.filter(pk=params.group_id).first()
        if group is None:
            return SaveStudentGroupResult(status='not_found')

        group.name = params.name
        group.save()
        group.students.set(params.student_ids)
        return SaveStudentGroupResult(status='updated', group_id=str(group.pk))

    def get_task_results_source_for_event(
        self,
        student_id: str,
        event_id: str,
    ):
        participation = EventParticipation.objects.filter(
            student_id=student_id,
            event_id=event_id,
        ).first()
        if not participation:
            return None

        mark = Mark.objects.filter(participation=participation).first()
        if not mark or not mark.task_scores:
            return None

        variant_tasks = []
        if participation.variant_id:
            variant_tasks = list(VariantTask.objects.filter(
                variant_id=participation.variant_id,
                is_assessable=True,
            ).order_by('order', 'pk'))
        candidate_task_ids = (
            [row.task_id for row in variant_tasks]
            if variant_tasks
            else list(mark.task_scores)
        )
        task_groups = TaskGroup.objects.filter(
            task_id__in=candidate_task_ids,
        ).select_related('group')
        return TaskResultsSource(
            task_scores=mark.task_scores,
            variant_tasks=tuple(
                TaskResultVariantRow(
                    variant_task_id=str(row.pk),
                    task_id=str(row.task_id),
                )
                for row in variant_tasks
            ),
            groups=tuple(
                TaskResultGroupRef(
                    task_id=str(membership.task_id),
                    group_id=str(membership.group_id),
                    group_name=membership.group.name,
                )
                for membership in task_groups
            ),
        )

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

    def get_student_remedial_source(
        self,
        student_id: str,
    ) -> StudentRemedialSource:
        task_logs = list(
            StudentTaskLog.objects.filter(
                student_id=student_id,
            ).select_related('analog_group', 'topic')
        )
        group_ids = {
            task_log.analog_group_id
            for task_log in task_logs
            if task_log.analog_group_id
        }
        memberships = list(
            TaskGroup.objects.filter(group_id__in=group_ids)
        )
        group_ids_by_task = defaultdict(list)
        for membership in memberships:
            group_ids_by_task[str(membership.task_id)].append(
                str(membership.group_id),
            )
        tasks = Task.objects.filter(
            id__in=group_ids_by_task,
        )
        return StudentRemedialSource(
            task_logs=tuple(
                StudentRemedialTaskLog(
                    task_id=str(task_log.task_id),
                    analog_group=(
                        ObjectRef(
                            pk=str(task_log.analog_group_id),
                            name=task_log.analog_group.name,
                        )
                        if task_log.analog_group_id
                        else None
                    ),
                    topic=(
                        ObjectRef(
                            pk=str(task_log.topic_id),
                            name=task_log.topic.name,
                        )
                        if task_log.topic_id
                        else None
                    ),
                    percentage=task_log.percentage,
                    is_correct=task_log.is_correct,
                )
                for task_log in task_logs
            ),
            tasks=tuple(
                StudentRemedialCandidateTask(
                    task_id=str(task.pk),
                    text=task.text,
                    analog_group_ids=group_ids_by_task[str(task.pk)],
                )
                for task in tasks
            ),
        )

    def get_group_name(self, group_id: str):
        group = StudentGroup.objects.filter(pk=group_id).first()
        return group.name if group else None

    def get_remedial_wizard_preview_source(
        self,
        group_id: str,
    ):
        group = StudentGroup.objects.filter(pk=group_id).first()
        if not group:
            return None

        students = list(group.get_active_students())
        task_logs = list(
            StudentTaskLog.objects.filter(
                student__in=students,
            ).values(
                'student_id',
                'task_id',
                'analog_group_id',
                'percentage',
            )
        )
        group_ids = {
            row['analog_group_id']
            for row in task_logs
            if row['analog_group_id']
        }
        memberships = list(
            TaskGroup.objects.filter(
                group_id__in=group_ids,
            ).select_related('task')
        )
        task_groups = defaultdict(list)
        tasks = {}
        for membership in memberships:
            task_id = str(membership.task_id)
            task_groups[task_id].append(str(membership.group_id))
            tasks[task_id] = membership.task

        return RemedialWizardPreviewSource(
            group=StudentGroupRef(pk=str(group.pk), name=group.name),
            students=tuple(self._student_detail(student) for student in students),
            task_logs=tuple(
                RemedialWizardTaskLog(
                    student_id=str(row['student_id']),
                    task_id=str(row['task_id']),
                    analog_group_id=(
                        str(row['analog_group_id'])
                        if row['analog_group_id']
                        else None
                    ),
                    percentage=row['percentage'],
                )
                for row in task_logs
            ),
            tasks=tuple(
                RemedialWizardTask(
                    task_id=task_id,
                    difficulty=task.difficulty or 1,
                    estimated_time=task.estimated_time or 0,
                    analog_group_ids=task_groups[task_id],
                )
                for task_id, task in tasks.items()
            ),
            analog_groups=tuple(
                RemedialWizardAnalogGroup(
                    group_id=str(analog_group.pk),
                    nominal_difficulty=analog_group.difficulty or 0,
                )
                for analog_group in AnalogGroup.objects.filter(pk__in=group_ids)
            ),
        )

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

    def get_task_log_sync_source(self, mark_id: str):
        mark = Mark.objects.select_related(
            'participation__student',
            'participation__event',
            'participation__variant',
        ).filter(pk=mark_id).first()
        if mark is None:
            return None

        participation = mark.participation
        variant_tasks = []
        if participation.variant_id:
            variant_tasks = list(
                VariantTask.objects.filter(
                    variant_id=participation.variant_id,
                    is_assessable=True,
                ).order_by('order', 'pk')
            )
            task_ids = {row.task_id for row in variant_tasks}
        else:
            task_ids = self._task_score_ids(mark.task_scores)
        tasks = list(
            Task.objects.select_related('topic', 'subtopic').filter(
                pk__in=task_ids,
            )
        )
        first_group_ids = {}
        for membership in TaskGroup.objects.filter(
            task_id__in=task_ids,
        ).order_by('pk'):
            first_group_ids.setdefault(
                str(membership.task_id),
                str(membership.group_id),
            )
        return TaskLogSyncSource(
            mark_id=str(mark.pk),
            student_id=str(participation.student_id),
            event_id=str(participation.event_id),
            variant_id=(
                str(participation.variant_id)
                if participation.variant_id
                else None
            ),
            completed_at=mark.checked_at or mark.created_at,
            task_scores=mark.task_scores,
            variant_tasks=tuple(
                TaskLogSyncVariantTask(
                    variant_task_id=str(row.pk),
                    task_id=str(row.task_id),
                )
                for row in variant_tasks
            ),
            tasks=tuple(
                TaskLogSyncTask(
                    task_id=str(task.pk),
                    topic_id=str(task.topic_id) if task.topic_id else None,
                    subtopic_id=(
                        str(task.subtopic_id)
                        if task.subtopic_id
                        else None
                    ),
                    analog_group_id=first_group_ids.get(str(task.pk)),
                    difficulty=task.difficulty,
                )
                for task in tasks
            ),
        )

    def apply_task_log_sync(self, plan: TaskLogSyncPlan) -> int:
        created_count = 0
        resolved_variant_task_ids = set()
        resolved_legacy_task_ids = set()
        for entry in plan.entries:
            if entry.variant_task_id:
                resolved_variant_task_ids.add(entry.variant_task_id)
            else:
                resolved_legacy_task_ids.add(entry.task_id)

            lookup = {'mark_id': plan.mark_id, 'task_id': entry.task_id}
            if entry.variant_task_id:
                lookup = {
                    'mark_id': plan.mark_id,
                    'variant_task_id': entry.variant_task_id,
                }
            _, created = StudentTaskLog.objects.update_or_create(
                **lookup,
                defaults={
                    'student_id': entry.student_id,
                    'task_id': entry.task_id,
                    'event_id': entry.event_id,
                    'variant_id': entry.variant_id,
                    'variant_task_id': entry.variant_task_id,
                    'topic_id': entry.topic_id,
                    'subtopic_id': entry.subtopic_id,
                    'analog_group_id': entry.analog_group_id,
                    'difficulty': entry.difficulty,
                    'points': entry.points,
                    'max_points': entry.max_points,
                    'comment': entry.comment,
                    'completed_at': entry.completed_at,
                    'percentage': entry.percentage,
                    'is_correct': entry.is_correct,
                },
            )
            if created:
                created_count += 1

        current_logs = StudentTaskLog.objects.filter(mark_id=plan.mark_id)
        keep_filter = Q()
        if resolved_variant_task_ids:
            keep_filter |= Q(
                variant_task_id__in=resolved_variant_task_ids,
            )
        if resolved_legacy_task_ids:
            keep_filter |= Q(
                variant_task__isnull=True,
                task_id__in=resolved_legacy_task_ids,
            )
        if keep_filter:
            current_logs.exclude(keep_filter).delete()
        else:
            current_logs.delete()

        return created_count

    @staticmethod
    def _task_score_ids(task_scores):
        if not isinstance(task_scores, dict):
            return set()
        task_ids = set()
        for score_key, score_data in task_scores.items():
            if not isinstance(score_data, dict):
                continue
            task_ids.add(str(score_data.get('task_id') or score_key))
        return task_ids

    def sync_student_task_logs(self, mark_id: str) -> int:
        """Compatibility facade for callers not yet using the use case."""
        from core_logic.use_cases.sync_student_task_logs import (
            SyncStudentTaskLogsUseCase,
        )

        return SyncStudentTaskLogsUseCase(self).execute(mark_id)
