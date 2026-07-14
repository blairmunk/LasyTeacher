"""Django implementation of the work repository."""

from typing import Set

from core_logic.interfaces.work_repo import (
    CreateVariantParams,
    CreateWorkParams,
    IWorkRepository,
)
from events.models import EventParticipation
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class DjangoWorkRepository(IWorkRepository):
    def get_variant_task_ids(self, work_id: str) -> Set[str]:
        return {
            str(task_id)
            for task_id in VariantTask.objects.filter(
                variant__work_id=work_id
            ).values_list('task_id', flat=True)
        }

    def get_student_variant_task_ids(
        self,
        work_id: str,
        student_id: str,
        event_id: str,
    ) -> Set[str]:
        participation = EventParticipation.objects.filter(
            event_id=event_id,
            student_id=student_id,
            variant__work_id=work_id,
        ).select_related('variant').first()
        if not participation or not participation.variant_id:
            return set()

        return {
            str(task_id)
            for task_id in VariantTask.objects.filter(
                variant_id=participation.variant_id
            ).values_list('task_id', flat=True)
        }

    def create_work(self, params: CreateWorkParams) -> str:
        work = Work.objects.create(
            name=params.name,
            work_type=params.work_type,
            max_score=params.max_score,
            variant_counter=params.variant_counter,
        )
        return str(work.pk)

    def create_variant_with_tasks(self, params: CreateVariantParams) -> str:
        variant = Variant.objects.create(
            work_id=params.work_id,
            number=params.number,
            work_name_snapshot=params.work_name_snapshot,
            max_score_snapshot=params.max_score_snapshot,
            variant_type=params.variant_type,
            assigned_student_id=params.student_id,
            source_work_id=params.source_work_id,
        )

        task_map = {
            str(task.id): task
            for task in Task.objects.filter(id__in=params.task_ids)
        }
        for order, task_id in enumerate(params.task_ids, 1):
            task = task_map.get(task_id)
            if not task:
                continue
            points = task.difficulty or 1
            VariantTask.objects.create(
                variant=variant,
                task=task,
                order=order,
                weight=points,
                max_points=points,
            )

        return str(variant.pk)

