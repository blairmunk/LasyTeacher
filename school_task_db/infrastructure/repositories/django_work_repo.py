"""Django implementation of the work repository."""

from typing import List, Optional

from django.db import transaction
from django.db.models import Count, Sum

from core_logic.entities.work import (
    OrphanVariantRef,
    OrphanVariantListItem,
    OrphanVariantStudentRef,
    VariantDeleteInfo,
    VariantGenerationGroupSource,
    VariantGenerationWork,
)
from core_logic.entities.work_variant_composition import (
    AvailableVariantTask,
    WorkVariantCompositionPlan,
    WorkVariantCompositionSaveResult,
    WorkVariantCompositionSource,
    WorkVariantContentBlock,
    WorkVariantSpecSourceRow,
    WorkTheorySubtopicSource,
    WorkTheoryTopicSource,
)
from core_logic.entities.work_spec_sync import (
    WorkSpecSyncItem,
    WorkSpecSyncSaveResult,
    WorkSpecSyncSource,
)
from core_logic.interfaces.orphan_variant_repo import (
    CreatedWorkFromOrphanVariantsRef,
    CreateWorkFromOrphanVariantsParams,
    IOrphanVariantRepository,
)
from core_logic.interfaces.variant_lifecycle_repo import (
    IVariantLifecycleRepository,
)
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
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from events.models import EventParticipation
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from task_groups.models import TaskGroup
from tasks.models import Task
from works.models import (
    Variant,
    VariantTask,
    Work,
    WorkAnalogGroup,
    WorkContentBlock,
    VariantContentBlockSnapshot,
)


def _variant_display_name(variant):
    return resolve_variant_display_name(
        work_name=variant.work.name if variant.work else '',
        work_name_snapshot=variant.work_name_snapshot,
        variant_type=variant.variant_type,
        assigned_student_name=(
            variant.assigned_student.get_short_name()
            if variant.assigned_student
            else ''
        ),
    )


class DjangoWorkRepository(
    IWorkRepository,
    IWorkVariantGenerationRepository,
    IOrphanVariantRepository,
    IVariantLifecycleRepository,
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

    def get_orphan_variants(self):
        return [
            OrphanVariantListItem(
                pk=str(variant.pk),
                display_name=_variant_display_name(variant),
                short_uuid=variant.get_short_uuid(),
                variant_type=variant.variant_type,
                task_count=variant.task_count,
                total_max_points=variant.total_max_points_value or 0,
                created_at=variant.created_at,
                assigned_student=(
                    OrphanVariantStudentRef(
                        pk=str(variant.assigned_student.pk),
                        short_name=variant.assigned_student.get_short_name(),
                    )
                    if variant.assigned_student
                    else None
                ),
            )
            for variant in Variant.objects.filter(
                work__isnull=True,
            ).select_related(
                'assigned_student',
            ).annotate(
                task_count=Count('varianttask'),
                total_max_points_value=Sum('varianttask__max_points'),
            ).order_by('-created_at')
        ]

    def count_orphan_variants(self) -> int:
        return Variant.objects.filter(work__isnull=True).count()

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
                self._persist_variant_content(variant, variant_plan)

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

    def get_orphan_variant_refs(
        self,
        variant_ids: List[str],
    ) -> List[OrphanVariantRef]:
        return [
            OrphanVariantRef(
                pk=str(variant.pk),
                variant_type=variant.variant_type,
                total_max_points=variant.total_max_points_value or 0,
            )
            for variant in Variant.objects.filter(
                pk__in=variant_ids,
                work__isnull=True,
            ).annotate(
                total_max_points_value=Sum('varianttask__max_points'),
            ).order_by('created_at')
        ]

    def create_work_from_orphan_variants(
        self,
        params: CreateWorkFromOrphanVariantsParams,
    ) -> Optional[CreatedWorkFromOrphanVariantsRef]:
        with transaction.atomic():
            variants = list(
                Variant.objects.select_for_update().filter(
                    pk__in=params.variant_ids,
                    work__isnull=True,
                ).order_by('created_at')
            )
            if len(variants) != len(params.variant_ids):
                return None

            work_id = self._create_work(
                CreateWorkParams(
                    name=params.name,
                    work_type=params.work_type,
                    max_score=params.max_score,
                    variant_counter=len(variants),
                )
            )
            variant_by_id = {str(variant.pk): variant for variant in variants}
            for number, variant_id in enumerate(params.variant_ids, 1):
                variant = variant_by_id[variant_id]
                variant.work_id = work_id
                variant.number = number
                variant.work_name_snapshot = params.name
                variant.max_score_snapshot = params.max_score
            Variant.objects.bulk_update(
                variants,
                [
                    'work',
                    'number',
                    'work_name_snapshot',
                    'max_score_snapshot',
                ],
            )
        return CreatedWorkFromOrphanVariantsRef(
            work_id=work_id,
            variant_count=len(variants),
        )

    def get_variant_delete_info(self, variant_id: str) -> Optional[VariantDeleteInfo]:
        variant = Variant.objects.select_related(
            'work',
            'assigned_student',
        ).filter(pk=variant_id).first()
        if variant is None:
            return None
        return VariantDeleteInfo(
            task_count=VariantTask.objects.filter(variant_id=variant_id).count(),
            participation_count=EventParticipation.objects.filter(
                variant_id=variant_id,
            ).count(),
            display_name=_variant_display_name(variant),
            short_uuid=variant.get_short_uuid(),
            work_id=str(variant.work_id or ''),
            work_name=variant.work.name if variant.work else '',
            total_max_points=(
                VariantTask.objects.filter(
                    variant_id=variant_id,
                ).aggregate(total=Sum('max_points'))['total']
                or 0
            ),
        )

    def detach_variant_from_work(self, variant_id: str) -> str:
        variant = Variant.objects.get(pk=variant_id)
        variant_short_id = variant.get_short_uuid()
        variant.work = None
        variant.save()
        return variant_short_id

    def delete_variant(self, variant_id: str) -> str:
        variant = Variant.objects.get(pk=variant_id)
        work_id = str(variant.work_id or '')
        variant.delete()
        return work_id

    def bulk_delete_work_variants(self, work_id: str, variant_ids: List[str]) -> int:
        return Variant.objects.filter(
            pk__in=variant_ids,
            work_id=work_id,
        ).delete()[0]

    def count_work_variants(self, work_id: str) -> int:
        return Variant.objects.filter(work_id=work_id).count()

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
        self._persist_variant_content(variant, plan)
        return str(variant.pk)

    @staticmethod
    def _persist_variant_content(variant, plan):
        task_snapshots = DjangoWorkRepository._task_snapshots(
            task_plan.task_id for task_plan in plan.tasks
        )
        VariantTask.objects.bulk_create(
            [
                VariantTask(
                    variant=variant,
                    task_id=task_plan.task_id,
                    task_snapshot=task_snapshots[
                        str(task_plan.task_id)
                    ].to_mapping(),
                    source_selection_id=task_plan.source_selection_id,
                    content_order=task_plan.content_order,
                    order=task_plan.order,
                    max_points=task_plan.max_points,
                    weight=task_plan.weight,
                    bank_role=task_plan.bank_role,
                    render_mode=task_plan.render_mode,
                    is_assessable=task_plan.is_assessable,
                    blank_cells_after=task_plan.blank_cells_after,
                    blank_cells_rows=task_plan.blank_cells_rows,
                )
                for task_plan in plan.tasks
            ]
        )
        VariantContentBlockSnapshot.objects.bulk_create(
            [
                VariantContentBlockSnapshot(
                    variant=variant,
                    source_content_id=block.source_content_id,
                    content_type=block.content_type,
                    order=block.order,
                    title=block.title,
                    content=dict(block.content),
                )
                for block in plan.content_blocks
            ]
        )

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

    @staticmethod
    def _task_snapshots(task_ids):
        tasks = Task.objects.filter(pk__in=set(task_ids)).select_related(
            'topic',
            'subtopic',
            'source',
        ).prefetch_related(
            'codifier_requirements__codifier',
            'images',
        )
        return build_task_content_snapshots(tasks)

    @staticmethod
    def _task_bank_roles(analog_group_id):
        return tuple(
            TaskGroup.objects.filter(
                group_id=analog_group_id,
            ).order_by('pk').values_list('bank_role', flat=True)
        )
