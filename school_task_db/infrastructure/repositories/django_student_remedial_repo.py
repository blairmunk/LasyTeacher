"""Django repository for student remedial planning sources."""

from collections import defaultdict

from core_logic.entities.student import (
    ObjectRef,
    RemedialWizardAnalogGroup,
    RemedialWizardPreviewSource,
    RemedialWizardTask,
    RemedialWizardTaskLog,
    StudentGroupRef,
    StudentRemedialCandidateTask,
    StudentRemedialSource,
    StudentRemedialTaskLog,
    TaskResultGroupRef,
    TaskResultsSource,
    TaskResultVariantRow,
)
from core_logic.interfaces.student_remedial_repo import (
    IStudentRemedialRepository,
)
from core_logic.value_objects.task_scores import TaskScoreRecord
from events.models import EventParticipation
from infrastructure.repositories.django_student_learning_support import (
    first_analog_groups,
    latest_task_history,
    result_is_correct,
    result_percentage,
    student_detail,
)
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from infrastructure.services.django_captured_task_result_queries import (
    captured_task_result_snapshot,
)
from students.models import StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task


class DjangoStudentRemedialRepository(IStudentRemedialRepository):
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

        task_results = tuple(
            captured
            for result in attempt.captured_task_results
            if (captured := captured_task_result_snapshot(result)) is not None
            and captured.is_assessable
        )
        task_scores = []
        variant_tasks = []
        for result in task_results:
            variant_task_id = result.variant_task_id
            score_key = variant_task_id or result.task.task_id
            task_scores.append(
                TaskScoreRecord(
                    score_key=score_key,
                    task_id=result.task.task_id,
                    variant_task_id=variant_task_id,
                    points=result.points,
                    max_points=result.max_points,
                    comment=result.comment,
                )
            )
            if variant_task_id:
                variant_tasks.append(TaskResultVariantRow(
                    variant_task_id=variant_task_id,
                    task_id=result.task.task_id,
                ))
        candidate_task_ids = [
            result.task.task_id
            for result in task_results
        ]
        task_groups = TaskGroup.objects.filter(
            task_id__in=candidate_task_ids,
        ).select_related('group')
        return TaskResultsSource(
            task_scores=tuple(task_scores),
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

    def get_student_remedial_source(
        self,
        student_id: str,
    ) -> StudentRemedialSource:
        task_results = latest_task_history([student_id])
        analog_groups = first_analog_groups(
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
                    percentage=result_percentage(result),
                    is_correct=result_is_correct(result),
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
        task_results = latest_task_history(
            [student.pk for student in students],
        )
        analog_groups_by_task = first_analog_groups(
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
            students=tuple(student_detail(student) for student in students),
            task_logs=tuple(
                RemedialWizardTaskLog(
                    student_id=result.student_id,
                    task_id=result.task.task_id,
                    analog_group_id=(
                        str(analog_groups_by_task[result.task.task_id].pk)
                        if result.task.task_id in analog_groups_by_task
                        else None
                    ),
                    percentage=result_percentage(result),
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
