"""Django adapter for composing variants from work specifications."""

from typing import Optional

from django.db import transaction

from core_logic.entities.work_variant_composition import (
    AvailableVariantTask,
    WorkTheorySubtopicSource,
    WorkTheoryTopicSource,
    WorkVariantCompositionPlan,
    WorkVariantCompositionSaveResult,
    WorkVariantCompositionSource,
    WorkVariantContentBlock,
    WorkVariantSpecSourceRow,
)
from core_logic.interfaces.work_variant_composition_repo import (
    IWorkVariantCompositionRepository,
)
from infrastructure.repositories.django_variant_content_persistence import (
    persist_variant_content,
)
from task_groups.models import TaskGroup
from works.models import (
    Variant,
    Work,
    WorkAnalogGroup,
    WorkContentBlock,
)


class DjangoWorkVariantCompositionRepository(
    IWorkVariantCompositionRepository,
):
    def get_variant_composition_source(
        self,
        work_id: str,
    ) -> Optional[WorkVariantCompositionSource]:
        work = Work.objects.select_for_update().filter(pk=work_id).first()
        if work is None:
            return None
        work_groups = list(
            WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).order_by('order', 'pk')
        )
        content_blocks = list(
            WorkContentBlock.objects.filter(
                work_id=work_id,
            ).prefetch_related(
                'topics__subtopics',
            ).order_by('order', 'pk')
        )
        return WorkVariantCompositionSource(
            work_name=work.name,
            duration=work.duration,
            max_score=work.max_score,
            variant_counter=work.variant_counter,
            assessment_mode=work.assessment_mode,
            spec_rows=tuple(
                self._variant_composition_spec_source_row(work_group)
                for work_group in work_groups
            ),
            content_blocks=tuple(
                self._variant_composition_content_block(block)
                for block in content_blocks
            ),
        )

    def save_variant_composition_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: WorkVariantCompositionPlan,
    ) -> WorkVariantCompositionSaveResult:
        with transaction.atomic():
            work = Work.objects.select_for_update().filter(pk=work_id).first()
            if work is None:
                return WorkVariantCompositionSaveResult(
                    status='not_found',
                )
            if work.variant_counter != expected_variant_counter:
                return WorkVariantCompositionSaveResult(
                    status='conflict',
                )

            for variant_plan in plan.variants:
                variant = Variant.objects.create(
                    work=work,
                    number=variant_plan.number,
                    work_name_snapshot=variant_plan.work_name_snapshot,
                    max_score_snapshot=variant_plan.max_score_snapshot,
                    duration_snapshot=variant_plan.duration_snapshot,
                )
                persist_variant_content(variant, variant_plan)

            work.variant_counter = plan.next_variant_counter
            work.save()
            return WorkVariantCompositionSaveResult(status='saved')

    @staticmethod
    def _variant_composition_spec_source_row(work_group):
        task_groups = TaskGroup.objects.filter(
            group=work_group.analog_group,
        )
        return WorkVariantSpecSourceRow(
            spec_row_id=str(work_group.pk),
            count=work_group.count,
            weight=work_group.weight,
            content_order=work_group.order,
            available_tasks=tuple(
                AvailableVariantTask(
                    task_id=str(task_group.task_id),
                    bank_role=task_group.bank_role,
                )
                for task_group in task_groups.order_by('pk')
            ),
            bank_role_filter=work_group.bank_role_filter,
            render_mode=work_group.render_mode,
            is_assessable=work_group.is_assessable,
            blank_cells_after=work_group.blank_cells_after,
            blank_space_area_cm2=work_group.blank_space_area_cm2,
            page_break_after=work_group.page_break_after,
        )

    @staticmethod
    def _variant_composition_content_block(block):
        return WorkVariantContentBlock(
            source_content_id=str(block.pk),
            content_type=block.content_type,
            order=block.order,
            title=block.title,
            body=block.body,
            topics=tuple(
                WorkTheoryTopicSource(
                    topic_id=str(topic.pk),
                    name=topic.name,
                    subject=topic.subject,
                    section=topic.section,
                    grade_level=topic.grade_level,
                    content=topic.description,
                    subtopics=tuple(
                        WorkTheorySubtopicSource(
                            subtopic_id=str(subtopic.pk),
                            name=subtopic.name,
                            content=subtopic.description,
                        )
                        for subtopic in topic.subtopics.all()
                    ),
                )
                for topic in block.topics.all()
            ),
            include_subtopics=block.include_subtopics,
        )
