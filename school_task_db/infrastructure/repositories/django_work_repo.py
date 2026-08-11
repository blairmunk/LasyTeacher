"""Django implementation of the work repository."""

from typing import List, Optional

from django.db import transaction

from core_logic.interfaces.work_repo import (
    CreatedWorkWithVariantsRef,
    CreatedWorkVariantRef,
    CreateVariantParams,
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    CreateWorkWithVariantsParams,
    CreateWorkWithVariantFromTasksParams,
    IWorkRepository,
    WorkContentBlockParams,
    WorkTaskSelectionParams,
    WorkUpdateContext,
)
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from infrastructure.repositories.django_variant_content_persistence import (
    persist_variant_content,
)
from tasks.models import Task
from works.models import (
    Variant,
    VariantTask,
    Work,
    WorkAnalogGroup,
    WorkContentBlock,
)


class DjangoWorkRepository(IWorkRepository):

    def _create_work(self, params: CreateWorkParams) -> str:
        work = Work.objects.create(
            name=params.name,
            work_type=params.work_type,
            duration=params.duration,
            max_score=params.max_score,
            variant_counter=params.variant_counter,
            assessment_mode=params.assessment_mode,
        )
        return str(work.pk)

    def get_work_update_context(self, work_id: str):
        work = Work.objects.filter(pk=work_id).first()
        if work is None:
            return None
        return WorkUpdateContext(
            work_id=str(work.pk),
            assessment_mode=work.assessment_mode,
            has_variants=work.variant_set.exists(),
            has_events=work.event_set.exists(),
        )

    def update_work_with_specification(self, params):
        with transaction.atomic():
            work = Work.objects.select_for_update().filter(
                pk=params.work.work_id,
            ).first()
            if work is None:
                return False
            work.name = params.work.name
            work.work_type = params.work.work_type
            work.duration = params.work.duration
            work.max_score = params.work.max_score
            work.assessment_mode = params.work.assessment_mode
            work.save()
            self._replace_work_content_plan(
                work_id=str(work.pk),
                specs=params.specs,
                content_blocks=params.content_blocks,
            )
        return True

    def create_work_with_specification(
        self,
        params: CreateWorkWithSpecificationParams,
    ) -> str:
        with transaction.atomic():
            work = Work.objects.create(
                name=params.work.name,
                work_type=params.work.work_type,
                duration=params.work.duration,
                max_score=params.work.max_score,
                variant_counter=params.work.variant_counter,
                assessment_mode=params.work.assessment_mode,
            )
            WorkAnalogGroup.objects.bulk_create([
                WorkAnalogGroup(
                    work=work,
                    analog_group_id=spec.analog_group_id,
                    order=spec.order,
                    count=spec.count,
                    weight=spec.weight,
                    bank_role_filter=spec.bank_role_filter,
                    render_mode=spec.render_mode,
                    is_assessable=spec.is_assessable,
                    blank_cells_after=spec.blank_cells_after,
                    blank_cells_rows=spec.blank_cells_rows,
                )
                for spec in params.specs
            ])
            self._create_work_content_blocks(
                str(work.pk),
                params.content_blocks,
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

    def _replace_work_content_plan(
        self,
        work_id: str,
        specs: List[WorkTaskSelectionParams],
        content_blocks: List[WorkContentBlockParams],
    ):
        WorkAnalogGroup.objects.filter(work_id=work_id).delete()
        WorkContentBlock.objects.filter(work_id=work_id).delete()
        WorkAnalogGroup.objects.bulk_create([
            WorkAnalogGroup(
                work_id=work_id,
                analog_group_id=spec.analog_group_id,
                order=spec.order,
                count=spec.count,
                weight=spec.weight,
                bank_role_filter=spec.bank_role_filter,
                render_mode=spec.render_mode,
                is_assessable=spec.is_assessable,
                blank_cells_after=spec.blank_cells_after,
                blank_cells_rows=spec.blank_cells_rows,
            )
            for spec in specs
        ])
        self._create_work_content_blocks(work_id, content_blocks)

    @staticmethod
    def _create_work_content_blocks(
        work_id: str,
        content_blocks: List[WorkContentBlockParams],
    ):
        for params in content_blocks:
            block = WorkContentBlock.objects.create(
                work_id=work_id,
                content_type=params.content_type,
                order=params.order,
                title=params.title,
                body=params.body,
                include_subtopics=params.include_subtopics,
            )
            if params.topic_ids:
                block.topics.set(params.topic_ids)

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
