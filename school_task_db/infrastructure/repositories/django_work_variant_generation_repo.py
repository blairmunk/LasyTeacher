"""Django repository for composing variants from work specifications."""

from typing import Optional

from django.db import transaction

from core_logic.entities.work import (
    VariantGenerationGroupSource,
    VariantGenerationWork,
)
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
from core_logic.entities.work_spec_sync import (
    WorkSpecSyncItem,
    WorkSpecSyncSaveResult,
    WorkSpecSyncSource,
)
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)
from infrastructure.repositories.django_variant_content_persistence import (
    persist_variant_content,
)
from task_groups.models import TaskGroup
from works.models import (
    Variant,
    VariantTask,
    Work,
    WorkAnalogGroup,
    WorkContentBlock,
)


class DjangoWorkVariantGenerationRepository(
    IWorkVariantGenerationRepository,
):
    def get_work_generation_target(self, work_id: str):
        work = Work.objects.filter(pk=work_id).first()
        if work is None:
            return None

        return VariantGenerationWork(
            pk=str(work.pk),
            name=work.name,
            duration=work.duration,
            variant_counter=work.variant_counter,
            assessment_mode=work.assessment_mode,
        )

    def get_variant_generation_group_sources(self, work_id: str):
        return [
            VariantGenerationGroupSource(
                group_name=work_group.analog_group.name,
                requested_count=work_group.count,
                bank_role_filter=work_group.bank_role_filter,
                task_bank_roles=self._task_bank_roles(
                    work_group.analog_group_id,
                ),
            )
            for work_group in WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        ]

    def get_work_spec_sync_source(
        self,
        work_id: str,
    ) -> Optional[WorkSpecSyncSource]:
        work = Work.objects.select_for_update().filter(pk=work_id).first()
        if work is None:
            return None
        task_rows = list(
            VariantTask.objects.filter(
                variant__work=work,
            ).order_by(
                'variant__number',
                'variant_id',
                'order',
            ).values_list(
                'variant_id',
                'task_id',
            )
        )
        group_ids_by_task_id = {}
        for task_id, group_id in (
            TaskGroup.objects.filter(
                task_id__in={task_id for _, task_id in task_rows},
            ).order_by('pk').values_list('task_id', 'group_id')
        ):
            group_ids_by_task_id.setdefault(task_id, []).append(group_id)

        group_ids_by_variant_id = {}
        for variant_id, task_id in task_rows:
            group_ids_by_variant_id.setdefault(variant_id, []).extend(
                group_ids_by_task_id.get(task_id, ()),
            )

        return WorkSpecSyncSource(
            variant_counter=work.variant_counter,
            variant_group_ids=tuple(
                tuple(str(group_id) for group_id in group_ids)
                for group_ids in group_ids_by_variant_id.values()
            ),
        )

    def save_work_spec_sync_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: tuple[WorkSpecSyncItem, ...],
    ) -> WorkSpecSyncSaveResult:
        with transaction.atomic():
            work = Work.objects.select_for_update().filter(pk=work_id).first()
            if work is None:
                return WorkSpecSyncSaveResult(status='not_found')
            if work.variant_counter != expected_variant_counter:
                return WorkSpecSyncSaveResult(status='conflict')

            created_count = 0
            for item in plan:
                _, was_created = WorkAnalogGroup.objects.update_or_create(
                    work=work,
                    analog_group_id=item.analog_group_id,
                    defaults={
                        'count': item.count,
                        'order': item.order,
                    },
                )
                if was_created:
                    created_count += 1
            return WorkSpecSyncSaveResult(
                status='saved',
                created_count=created_count,
            )

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

    def _variant_composition_spec_source_row(self, work_group):
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
            blank_cells_rows=work_group.blank_cells_rows,
        )

    def _variant_composition_content_block(self, block):
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

    @staticmethod
    def _task_bank_roles(analog_group_id):
        return tuple(
            TaskGroup.objects.filter(
                group_id=analog_group_id,
            ).order_by('pk').values_list('bank_role', flat=True)
        )
