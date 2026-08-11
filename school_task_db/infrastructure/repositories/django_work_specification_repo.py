"""Django repository for saving work specifications."""

from typing import List

from django.db import transaction

from core_logic.interfaces.work_repo import (
    CreateWorkWithSpecificationParams,
    WorkContentBlockParams,
    WorkTaskSelectionParams,
    WorkUpdateContext,
)
from core_logic.interfaces.work_specification_repo import (
    IWorkSpecificationRepository,
)
from works.models import Work, WorkAnalogGroup, WorkContentBlock


class DjangoWorkSpecificationRepository(IWorkSpecificationRepository):
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
