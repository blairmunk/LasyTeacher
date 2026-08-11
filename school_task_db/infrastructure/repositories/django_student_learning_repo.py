"""Django student learning history repository."""

from collections import defaultdict
from typing import List

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    RemedialWizardAnalogGroup,
    RemedialWizardPreviewSource,
    RemedialWizardTask,
    RemedialWizardTaskLog,
    StudentDetail,
    StudentGroupRef,
    StudentParticipationProfile,
    StudentRemedialCandidateTask,
    StudentRemedialSource,
    StudentRemedialTaskLog,
    StudentTaskResultProfile,
    TaskResultGroupRef,
    TaskResultsSource,
    TaskResultVariantRow,
    WorkGroupRef,
    WorkRef,
)
from core_logic.interfaces.student_learning_repo import IStudentLearningRepository
from core_logic.value_objects.attempt_status import (
    resolve_historical_participation_status,
)
from events.models import EventParticipation
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from infrastructure.services.django_captured_task_result_queries import (
    latest_assessable_task_results,
)
from students.models import StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import WorkAnalogGroup


class DjangoStudentLearningRepository(IStudentLearningRepository):
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

        attempt = latest_attempts_by_participation(
            [participation.pk],
        ).get(participation.pk)
        if attempt is None:
            return None

        task_results = [
            result
            for result in attempt.captured_task_results
            if result.is_assessable_snapshot
        ]
        task_scores = {}
        variant_tasks = []
        for result in task_results:
            variant_task_id = str(result.variant_task_id or '')
            score_key = variant_task_id or result.task_id_snapshot
            task_scores[score_key] = {
                'task_id': result.task_id_snapshot,
                'variant_task_id': variant_task_id,
                'points': result.points,
                'max_points': (
                    result.checked_max_points
                    if result.checked_max_points is not None
                    else result.expected_max_points_snapshot
                ),
                'comment': result.comment,
            }
            if variant_task_id:
                variant_tasks.append(TaskResultVariantRow(
                    variant_task_id=variant_task_id,
                    task_id=result.task_id_snapshot,
                ))
        candidate_task_ids = [
            result.task_id_snapshot
            for result in task_results
        ]
        task_groups = TaskGroup.objects.filter(
            task_id__in=candidate_task_ids,
        ).select_related('group')
        return TaskResultsSource(
            task_scores=task_scores,
            variant_tasks=tuple(variant_tasks),
            groups=tuple(
                TaskResultGroupRef(
                    task_id=str(membership.task_id),
                    group_id=str(membership.group_id),
                    group_name=membership.group.name,
                )
                for membership in task_groups
            ),
        )

    def get_profile_participations(
        self,
        student_id: str,
    ) -> List[StudentParticipationProfile]:
        participations = list(
            EventParticipation.objects.filter(
                student_id=student_id,
            ).select_related(
                'event',
                'event__work',
                'variant',
            ).order_by('-event__planned_date')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participations),
            include_task_results=False,
        )

        rows = []
        for participation in participations:
            event = participation.event
            work = event.work if event else None
            attempt = attempts.get(participation.pk)
            event_name = attempt.event_name_snapshot if attempt else event.name
            event_date = (
                attempt.event_date_snapshot if attempt else event.planned_date
            )
            rows.append(
                StudentParticipationProfile(
                    participation=ObjectRef(
                        pk=str(participation.pk),
                        name=str(participation),
                    ),
                    event=EventRef(
                        pk=str(event.pk),
                        name=event_name,
                        planned_date=event_date,
                    ),
                    work=(
                        WorkRef(
                            pk=str(work.pk),
                            name=(
                                attempt.work_name_snapshot
                                if attempt
                                else work.name
                            ),
                            work_type=work.work_type,
                            work_type_display=work.get_work_type_display(),
                        )
                        if work
                        else None
                    ),
                    mark=(
                        MarkRef(
                            pk=str(attempt.mark_id),
                            score=attempt.score,
                            points=attempt.points,
                            max_points=attempt.max_points,
                            teacher_comment=attempt.teacher_comment,
                        )
                        if attempt
                        else None
                    ),
                    score=attempt.score if attempt else None,
                    is_absent=(
                        resolve_historical_participation_status(
                            participation.status,
                            has_attempt=attempt is not None,
                        ) == 'absent'
                    ),
                    variant_number=(
                        attempt.variant_number_snapshot
                        if attempt
                        else (
                            participation.variant.number
                            if participation.variant
                            else None
                        )
                    ),
                )
            )
        return rows

    def get_task_logs(self, student_id: str) -> List[StudentTaskResultProfile]:
        results = self._latest_task_history([student_id])
        analog_groups = self._first_analog_groups(
            result.task.task_id for result in results
        )
        return [
            StudentTaskResultProfile(
                task=ObjectRef(pk=result.task.task_id, name=result.task.text),
                event=ObjectRef(pk=result.event_id, name=result.event_name),
                topic_name=result.task.topic_name,
                analog_group=(
                    ObjectRef(
                        pk=str(analog_groups[result.task.task_id].pk),
                        name=analog_groups[result.task.task_id].name,
                    )
                    if result.task.task_id in analog_groups
                    else None
                ),
                difficulty=result.task.difficulty,
                points=result.points,
                max_points=result.max_points,
                is_correct=self._result_is_correct(result),
                percentage=self._result_percentage(result),
                completed_at=result.captured_at,
            )
            for result in sorted(
                results,
                key=lambda item: item.captured_at,
                reverse=True,
            )
        ]

    def get_student_remedial_source(
        self,
        student_id: str,
    ) -> StudentRemedialSource:
        task_results = self._latest_task_history([student_id])
        analog_groups = self._first_analog_groups(
            result.task.task_id for result in task_results
        )
        group_ids = {group.pk for group in analog_groups.values()}
        memberships = list(TaskGroup.objects.filter(group_id__in=group_ids))
        group_ids_by_task = defaultdict(list)
        for membership in memberships:
            group_ids_by_task[str(membership.task_id)].append(
                str(membership.group_id),
            )
        tasks = Task.objects.filter(id__in=group_ids_by_task)
        return StudentRemedialSource(
            task_logs=tuple(
                StudentRemedialTaskLog(
                    task_id=result.task.task_id,
                    analog_group=(
                        ObjectRef(
                            pk=str(analog_groups[result.task.task_id].pk),
                            name=analog_groups[result.task.task_id].name,
                        )
                        if result.task.task_id in analog_groups
                        else None
                    ),
                    topic=(
                        ObjectRef(
                            pk=result.task.topic_id,
                            name=result.task.topic_name,
                        )
                        if result.task.topic_id
                        else None
                    ),
                    percentage=self._result_percentage(result),
                    is_correct=self._result_is_correct(result),
                )
                for result in task_results
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

    def get_remedial_wizard_preview_source(self, group_id: str):
        group = StudentGroup.objects.filter(pk=group_id).first()
        if not group:
            return None

        students = list(
            group.students.all().order_by('last_name', 'first_name')
        )
        task_results = self._latest_task_history(
            [student.pk for student in students],
        )
        analog_groups_by_task = self._first_analog_groups(
            result.task.task_id for result in task_results
        )
        group_ids = {group.pk for group in analog_groups_by_task.values()}
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
                    student_id=result.student_id,
                    task_id=result.task.task_id,
                    analog_group_id=(
                        str(analog_groups_by_task[result.task.task_id].pk)
                        if result.task.task_id in analog_groups_by_task
                        else None
                    ),
                    percentage=self._result_percentage(result),
                )
                for result in task_results
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

    @staticmethod
    def _student_detail(student):
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

    @staticmethod
    def _latest_task_history(student_ids):
        participation_ids = EventParticipation.objects.filter(
            student_id__in=student_ids,
        ).values_list('pk', flat=True)
        return latest_assessable_task_results(participation_ids)

    @staticmethod
    def _first_analog_groups(task_ids):
        groups = {}
        for membership in TaskGroup.objects.filter(
            task_id__in=set(task_ids),
        ).select_related('group').order_by('pk'):
            groups.setdefault(str(membership.task_id), membership.group)
        return groups

    @staticmethod
    def _result_percentage(result):
        if not result.max_points or result.max_points <= 0:
            return None
        return round(result.points / result.max_points * 100, 1)

    @classmethod
    def _result_is_correct(cls, result):
        percentage = cls._result_percentage(result)
        return percentage >= 70 if percentage is not None else None
