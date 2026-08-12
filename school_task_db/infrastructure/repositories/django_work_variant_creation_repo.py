"""Django repository for persisting work variants."""

from django.db import transaction

from core_logic.entities.work_specification_commands import CreateWorkParams
from core_logic.entities.work_variant_creation_commands import (
    CreatedWorkVariantRef,
    CreatedWorkWithVariantsRef,
    CreateVariantParams,
    CreateWorkWithVariantFromTasksParams,
    CreateWorkWithVariantsParams,
)
from core_logic.interfaces.work_variant_creation_repo import (
    IWorkVariantCreationRepository,
)
from infrastructure.repositories.django_variant_content_persistence import (
    persist_variant_content,
)
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class DjangoWorkVariantCreationRepository(IWorkVariantCreationRepository):
    @staticmethod
    def _create_work(params: CreateWorkParams) -> str:
        work = Work.objects.create(
            name=params.name,
            work_type=params.work_type,
            duration=params.duration,
            max_score=params.max_score,
            variant_counter=params.variant_counter,
            assessment_mode=params.assessment_mode,
        )
        return str(work.pk)

    def create_work_with_variants(
        self,
        params: CreateWorkWithVariantsParams,
    ) -> CreatedWorkWithVariantsRef:
        with transaction.atomic():
            work_id = self._create_work(params.work)
            variant_ids = [
                self._create_variant_from_plan(
                    CreateVariantParams(
                        work_id=work_id,
                        student_id=variant.student_id,
                        plan=variant.plan,
                        source_work_id=variant.source_work_id,
                        source_participation_id=(
                            variant.source_participation_id
                        ),
                        source_attempt_snapshot_id=(
                            variant.source_attempt_snapshot_id
                        ),
                        variant_type=variant.variant_type,
                    )
                )
                for variant in params.variants
            ]
        return CreatedWorkWithVariantsRef(
            work_id=work_id,
            variant_ids=variant_ids,
        )

    def create_variant_from_plan(self, params: CreateVariantParams) -> str:
        with transaction.atomic():
            return self._create_variant_from_plan(params)

    def _create_variant_from_plan(self, params: CreateVariantParams) -> str:
        plan = params.plan
        variant = Variant.objects.create(
            work_id=params.work_id,
            number=plan.number,
            work_name_snapshot=plan.work_name_snapshot,
            max_score_snapshot=plan.max_score_snapshot,
            duration_snapshot=plan.duration_snapshot,
            variant_type=params.variant_type,
            assigned_student_id=params.student_id,
            source_work_id=params.source_work_id,
            source_participation_id=params.source_participation_id,
            source_attempt_snapshot_id=params.source_attempt_snapshot_id,
        )
        persist_variant_content(variant, plan)
        return str(variant.pk)

    def create_work_with_variant_from_tasks(
        self,
        params: CreateWorkWithVariantFromTasksParams,
    ) -> CreatedWorkVariantRef:
        with transaction.atomic():
            tasks = Task.objects.filter(pk__in=params.task_ids)
            task_map = {str(task.pk): task for task in tasks}
            ordered_tasks = [
                task_map[task_id]
                for task_id in params.task_ids
                if task_id in task_map
            ]
            if not ordered_tasks:
                return CreatedWorkVariantRef(
                    work_id='',
                    variant_id='',
                    tasks_count=0,
                )

            work = Work.objects.create(
                name=params.name,
                work_type=params.work_type,
            )
            variant = Variant.objects.create(
                work=work,
                number=1,
            )
            work.variant_counter = 1
            work.save(update_fields=['variant_counter'])

            for order, task in enumerate(ordered_tasks, 1):
                VariantTask.objects.create(
                    variant=variant,
                    task=task,
                    task_snapshot=build_task_content_snapshots(
                        [task],
                    )[str(task.pk)].to_mapping(),
                    order=order,
                )

        return CreatedWorkVariantRef(
            work_id=str(work.pk),
            variant_id=str(variant.pk),
            tasks_count=len(ordered_tasks),
        )
