"""Django implementation of the work repository."""

from typing import List, Optional, Set

from django.db import transaction
from django.db.models import Count, Sum

from core_logic.entities.work import (
    OrphanVariantRef,
    OrphanVariantListItem,
    OrphanVariantStudentRef,
    RemedialMarkRef,
    RemedialOriginalTaskRow,
    RemedialSheetData,
    RemedialTaskRef,
    RemedialTrainingTaskRow,
    RemedialVariantRef,
    VariantDeleteInfo,
    VariantDetailImage,
    VariantDetailRef,
    VariantDetailStudentRef,
    VariantDetailTask,
    VariantDetailTaskRow,
    VariantDetailVariant,
    VariantGenerationGroup,
    VariantGenerationWork,
    VariantListItem,
    VariantListStudentRef,
    VariantListWorkRef,
    WorkDetailAnalogGroup,
    WorkDetailSpecGroup,
    WorkDetailSpecPreviewItem,
    WorkDetailVariant,
    WorkDetailWork,
    WorkListItem,
)
from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_REMEDIAL,
)
from core_logic.value_objects.task_scores import task_score_records_by_task_id
from core_logic.interfaces.work_repo import (
    AttachVariantsToWorkParams,
    CreatedWorkVariantRef,
    CreateVariantParams,
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    CreateWorkWithVariantFromTasksParams,
    IWorkRepository,
    WorkSpecificationRowParams,
)
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.services.work_spec_sync_service import WorkSpecSyncService
from core_logic.services.work_score_allocation_service import (
    WorkScoreAllocationService,
    WorkScoreSpecRow,
)
from core_logic.services.work_variant_composition_service import (
    AvailableVariantTask,
    WorkVariantCompositionInput,
    WorkVariantCompositionService,
    WorkVariantSpecRow,
)
from events.models import EventParticipation, Mark
from task_groups.models import TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class DjangoWorkRepository(IWorkRepository, IWorkDocumentRepository):
    def get_list_works(self, filters=None):
        queryset = Work.objects.annotate(
            variant_count=Count('variant'),
        )
        if filters:
            if filters.q:
                queryset = queryset.filter(name__icontains=filters.q)
            if filters.work_type:
                queryset = queryset.filter(work_type=filters.work_type)
            if filters.hide_remedial:
                queryset = queryset.exclude(work_type='remedial')
            if filters.variant_status == 'with_variants':
                queryset = queryset.filter(variant_count__gt=0)
            elif filters.variant_status == 'without_variants':
                queryset = queryset.filter(variant_count=0)

        return [
            WorkListItem(
                pk=str(work.pk),
                name=work.name,
                duration=work.duration,
                created_at=work.created_at,
                variant_count=work.variant_count,
                work_type=work.work_type,
                work_type_display=work.get_work_type_display(),
            )
            for work in queryset.order_by('-created_at')
        ]

    def get_list_variants(self):
        return [
            VariantListItem(
                pk=str(variant.pk),
                number=variant.number,
                created_at=variant.created_at,
                task_count=variant.task_count,
                display_name=variant.display_name,
                variant_type=variant.variant_type,
                variant_type_display=variant.get_variant_type_display(),
                work=(
                    VariantListWorkRef(
                        pk=str(variant.work.pk),
                        name=variant.work.name,
                        duration=variant.work.duration,
                    )
                    if variant.work
                    else None
                ),
                assigned_student=(
                    VariantListStudentRef(
                        pk=str(variant.assigned_student.pk),
                        short_name=variant.assigned_student.get_short_name(),
                    )
                    if variant.assigned_student
                    else None
                ),
                has_source_work=bool(variant.source_work_id),
            )
            for variant in Variant.objects.select_related(
                'work',
                'assigned_student',
            ).annotate(
                task_count=Count('varianttask'),
            ).order_by('-created_at')
        ]

    def get_work_form_analog_group_options(self):
        from task_groups.models import AnalogGroup

        return AnalogGroup.objects.all()

    def get_work_name(self, work_id: str):
        return Work.objects.filter(pk=work_id).values_list('name', flat=True).first()

    def get_work_generation_target(self, work_id: str):
        work = Work.objects.filter(pk=work_id).first()
        if work is None:
            return None

        return VariantGenerationWork(
            pk=str(work.pk),
            name=work.name,
            duration=work.duration,
            variant_counter=work.variant_counter,
        )

    def get_variant_generation_groups(self, work_id: str):
        return [
            VariantGenerationGroup(
                group_name=work_group.analog_group.name,
                requested_count=work_group.count,
                available_count=self._count_available_group_tasks(work_group),
                bank_role_filter=work_group.bank_role_filter,
            )
            for work_group in WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        ]

    def get_work_detail(self, work_id: str):
        work = Work.objects.filter(pk=work_id).first()
        if work is None:
            return None

        return WorkDetailWork(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            work_type_display=work.get_work_type_display(),
            duration=work.duration,
            max_score=work.max_score,
            effective_max_score=work.effective_max_score,
            variant_count=Variant.objects.filter(work_id=work_id).count(),
            created_at=work.created_at,
            updated_at=work.updated_at,
        )

    def get_detail_variants(self, work_id: str):
        return [
            WorkDetailVariant(
                pk=str(variant.pk),
                number=variant.number,
                short_uuid=variant.get_short_uuid(),
                task_count=variant.tasks.count(),
                total_max_points=variant.total_max_points,
                created_at=variant.created_at,
                variant_type=variant.variant_type,
                has_assigned_student=bool(variant.assigned_student_id),
            )
            for variant in Variant.objects.filter(work_id=work_id)
        ]

    def get_detail_analog_groups(self, work_id: str):
        return [
            self._build_work_detail_spec_group(work_group)
            for work_group in WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        ]

    def get_spec_preview(self, work_id: str):
        work = Work.objects.get(pk=work_id)
        work_groups = list(
            WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        )
        groups_by_id = {
            str(work_group.pk): work_group
            for work_group in work_groups
        }
        preview_by_group_id = {}
        for allocation in WorkScoreAllocationService().allocate(
            max_score=work.max_score,
            spec_rows=(
                WorkScoreSpecRow(
                    spec_row_id=str(work_group.pk),
                    count=work_group.count,
                    weight=work_group.weight,
                    is_assessable=work_group.is_assessable,
                )
                for work_group in work_groups
            ),
        ):
            preview = preview_by_group_id.setdefault(
                allocation.spec_row_id,
                {
                    'per_task': allocation.points,
                    'total_points': 0,
                },
            )
            preview['total_points'] += allocation.points

        return [
            WorkDetailSpecPreviewItem(
                wg=self._build_work_detail_spec_group(
                    groups_by_id[group_id],
                ),
                per_task=preview['per_task'],
                total_points=preview['total_points'],
                available_count=self._count_available_group_tasks(
                    groups_by_id[group_id],
                ),
            )
            for group_id, preview in preview_by_group_id.items()
        ]

    def _build_work_detail_spec_group(self, work_group):
        return WorkDetailSpecGroup(
            order=work_group.order,
            analog_group=WorkDetailAnalogGroup(
                pk=str(work_group.analog_group.pk),
                name=work_group.analog_group.name,
                task_count=TaskGroup.objects.filter(
                    group=work_group.analog_group,
                ).count(),
            ),
            count=work_group.count,
            weight=work_group.weight,
            bank_role_filter=work_group.bank_role_filter,
            render_mode=work_group.render_mode,
            is_assessable=work_group.is_assessable,
            blank_cells_after=work_group.blank_cells_after,
            blank_cells_rows=work_group.blank_cells_rows,
        )

    def get_variant_detail(self, variant_id: str):
        variant = Variant.objects.select_related(
            'work',
            'assigned_student',
            'source_work',
        ).filter(pk=variant_id).first()
        if variant is None:
            return None

        return VariantDetailVariant(
            pk=str(variant.pk),
            number=variant.number,
            display_name=variant.display_name,
            short_uuid=variant.get_short_uuid(),
            medium_uuid=variant.get_medium_uuid(),
            variant_type=variant.variant_type,
            variant_type_display=variant.get_variant_type_display(),
            display_duration=variant.display_duration,
            display_max_score=variant.display_max_score,
            created_at=variant.created_at,
            work=(
                VariantDetailRef(
                    pk=str(variant.work.pk),
                    name=variant.work.name,
                    short_uuid=variant.work.get_short_uuid(),
                )
                if variant.work
                else None
            ),
            assigned_student=(
                VariantDetailStudentRef(
                    pk=str(variant.assigned_student.pk),
                    full_name=variant.assigned_student.get_full_name(),
                    short_name=variant.assigned_student.get_short_name(),
                )
                if variant.assigned_student
                else None
            ),
            source_work=(
                VariantDetailRef(
                    pk=str(variant.source_work.pk),
                    name=variant.source_work.name,
                    short_uuid=variant.source_work.get_short_uuid(),
                )
                if variant.source_work
                else None
            ),
        )

    def get_variant_detail_tasks(self, variant_id: str):
        variant_tasks = VariantTask.objects.filter(
            variant_id=variant_id,
        ).select_related(
            'task',
            'task__topic',
            'task__subtopic',
        ).prefetch_related(
            'task__images',
        ).order_by('order')

        return [
            VariantDetailTaskRow(
                task=VariantDetailTask(
                    pk=str(variant_task.task.pk),
                    id=str(variant_task.task.pk),
                    topic=str(variant_task.task.topic),
                    text=variant_task.task.text,
                    answer=variant_task.task.answer,
                    task_type_display=variant_task.task.get_task_type_display(),
                    difficulty=variant_task.task.difficulty,
                    short_uuid=variant_task.task.get_short_uuid(),
                    images=[
                        VariantDetailImage(
                            caption=image.caption,
                            position=image.position,
                            safe_url=image.safe_url,
                            css_class=image.get_css_class(),
                        )
                        for image in variant_task.task.images.all()
                    ],
                ),
                order=variant_task.order,
                max_points=variant_task.max_points,
                bank_role=variant_task.bank_role,
                render_mode=variant_task.render_mode,
                is_assessable=variant_task.is_assessable,
                blank_cells_after=variant_task.blank_cells_after,
                blank_cells_rows=variant_task.blank_cells_rows,
            )
            for variant_task in variant_tasks
        ]

    def get_variant_total_max_points(self, variant_id: str) -> int:
        variant = Variant.objects.get(pk=variant_id)
        return variant.total_max_points

    def get_variant_type(self, variant_id: str):
        return (
            Variant.objects.filter(pk=variant_id)
            .values_list('variant_type', flat=True)
            .first()
        )

    def get_remedial_sheet_data(
        self,
        variant_id: str,
    ) -> Optional[RemedialSheetData]:
        variant = Variant.objects.select_related(
            'assigned_student',
            'source_work',
            'work',
        ).filter(pk=variant_id).first()
        if variant is None:
            return None
        student = variant.assigned_student
        source_work = variant.source_work
        mark = None
        original_tasks = []

        if source_work and student:
            original_ep = EventParticipation.objects.filter(
                event__work=source_work,
                student=student,
            ).select_related('variant').first()

            if original_ep:
                mark = Mark.objects.filter(participation=original_ep).first()
                task_scores_by_task_id = task_score_records_by_task_id(
                    mark.task_scores if mark else {},
                )

                if original_ep.variant:
                    original_variant_tasks = VariantTask.objects.filter(
                        variant=original_ep.variant,
                    ).select_related(
                        'task',
                        'task__topic',
                        'task__subtopic',
                        'task__source',
                    ).order_by('order')

                    for variant_task in original_variant_tasks:
                        task = variant_task.task
                        score_record = task_scores_by_task_id.get(str(task.pk))
                        points = score_record.points if score_record else None
                        max_points = (
                            score_record.max_points
                            if score_record
                            else None
                        )
                        pct, status = self._score_status(points, max_points)
                        task_group = TaskGroup.objects.filter(task=task).first()

                        original_tasks.append(
                            RemedialOriginalTaskRow(
                                task=self._remedial_task_ref(task),
                                order=variant_task.order,
                                points=points,
                                max_points=max_points,
                                pct=pct,
                                status=status,
                                group_name=(
                                    task_group.group.name
                                    if task_group
                                    else ''
                                ),
                            )
                        )

        new_tasks = VariantTask.objects.filter(
            variant=variant,
        ).select_related(
            'task',
            'task__topic',
            'task__subtopic',
            'task__source',
        ).order_by('order')

        return RemedialSheetData(
            variant=RemedialVariantRef(
                pk=str(variant.pk),
                work=(
                    VariantDetailRef(
                        pk=str(variant.work.pk),
                        name=variant.work.name,
                    )
                    if variant.work
                    else None
                ),
            ),
            student=(
                VariantDetailStudentRef(
                    pk=str(student.pk),
                    full_name=student.get_full_name(),
                    short_name=student.get_short_name(),
                )
                if student
                else None
            ),
            source_work=(
                VariantDetailRef(
                    pk=str(source_work.pk),
                    name=source_work.name,
                )
                if source_work
                else None
            ),
            mark=(
                RemedialMarkRef(
                    score=mark.score,
                    points=mark.points,
                    max_points=mark.max_points,
                )
                if mark
                else None
            ),
            original_tasks=original_tasks,
            new_tasks=[
                RemedialTrainingTaskRow(
                    pk=str(variant_task.pk),
                    task_id=str(variant_task.task_id),
                    task=self._remedial_task_ref(variant_task.task),
                    order=variant_task.order,
                    max_points=variant_task.max_points,
                    bank_role=variant_task.bank_role,
                    render_mode=variant_task.render_mode,
                    is_assessable=variant_task.is_assessable,
                    blank_cells_after=variant_task.blank_cells_after,
                    blank_cells_rows=variant_task.blank_cells_rows,
                )
                for variant_task in new_tasks
            ],
        )

    @staticmethod
    def _remedial_task_ref(task):
        return RemedialTaskRef(
            pk=str(task.pk),
            text=task.text,
            answer=task.answer,
            short_solution=task.short_solution,
            full_solution=task.full_solution,
            hint=task.hint,
            instruction=task.instruction,
            task_type=task.task_type,
            difficulty=task.difficulty,
            topic=task.topic.name if task.topic else '',
            subtopic=task.subtopic.name if task.subtopic else '',
            source=str(task.source) if task.source else '',
            source_detail=task.source_detail,
        )

    def get_work_remedial_variant_ids(self, work_id: str) -> List[str]:
        return [
            str(variant_id)
            for variant_id in Variant.objects.filter(
                work_id=work_id,
                variant_type='remedial',
            ).order_by(
                'number',
                'pk',
            ).values_list(
                'pk',
                flat=True,
            )
        ]

    def get_work_variant_ids(self, work_id: str) -> List[str]:
        return [
            str(variant_id)
            for variant_id in Variant.objects.filter(
                work_id=work_id,
            ).order_by(
                'number',
                'pk',
            ).values_list(
                'pk',
                flat=True,
            )
        ]

    def _score_status(self, points, max_points):
        if (
            isinstance(points, (int, float))
            and isinstance(max_points, (int, float))
            and max_points > 0
        ):
            pct = points / max_points * 100
            if pct >= 70:
                status = 'ok'
            elif pct > 0:
                status = 'partial'
            else:
                status = 'fail'
            return round(pct, 1), status

        return 0, 'unknown'

    def get_orphan_variants(self):
        return [
            OrphanVariantListItem(
                pk=str(variant.pk),
                display_name=variant.display_name,
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

    def sync_analog_groups_from_variants(
        self,
        work_id: str,
    ) -> Optional[int]:
        with transaction.atomic():
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

            plan = WorkSpecSyncService().build_plan(
                group_ids_by_variant_id.values(),
            )
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
            return created_count

    def compose_variants(self, work_id: str, count: int) -> Optional[int]:
        with transaction.atomic():
            work = Work.objects.select_for_update().filter(pk=work_id).first()
            if work is None:
                return None
            work_groups = list(
                WorkAnalogGroup.objects.filter(
                    work_id=work_id,
                ).order_by('order', 'pk')
            )
            composition_plan = WorkVariantCompositionService().compose(
                WorkVariantCompositionInput(
                    work_name=work.name,
                    duration=work.duration,
                    max_score=work.max_score,
                    effective_max_score=(
                        work.max_score
                        or sum(
                            group.weight * group.count
                            for group in work_groups
                            if group.is_assessable
                        )
                    ),
                    variant_counter=work.variant_counter,
                    spec_rows=tuple(
                        self._variant_composition_spec_row(work_group)
                        for work_group in work_groups
                    ),
                ),
                count=count,
            )
            for variant_plan in composition_plan.variants:
                variant = Variant.objects.create(
                    work=work,
                    number=variant_plan.number,
                    work_name_snapshot=variant_plan.work_name_snapshot,
                    max_score_snapshot=variant_plan.max_score_snapshot,
                    duration_snapshot=variant_plan.duration_snapshot,
                )
                VariantTask.objects.bulk_create(
                    [
                        VariantTask(
                            variant=variant,
                            task_id=task_plan.task_id,
                            order=task_plan.order,
                            max_points=task_plan.max_points,
                            weight=task_plan.weight,
                            bank_role=task_plan.bank_role,
                            render_mode=task_plan.render_mode,
                            is_assessable=task_plan.is_assessable,
                            blank_cells_after=task_plan.blank_cells_after,
                            blank_cells_rows=task_plan.blank_cells_rows,
                        )
                        for task_plan in variant_plan.tasks
                    ]
                )

            work.variant_counter = composition_plan.next_variant_counter
            work.save()
            return len(composition_plan.variants)

    def _variant_composition_spec_row(self, work_group):
        task_groups = TaskGroup.objects.filter(
            group=work_group.analog_group,
        )
        if work_group.bank_role_filter != TASK_BANK_ROLE_ANY:
            task_groups = task_groups.filter(
                bank_role=work_group.bank_role_filter,
            )
        return WorkVariantSpecRow(
            spec_row_id=str(work_group.pk),
            count=work_group.count,
            weight=work_group.weight,
            available_tasks=tuple(
                AvailableVariantTask(
                    task_id=str(task_group.task_id),
                    bank_role=task_group.bank_role,
                )
                for task_group in task_groups.order_by('pk')
            ),
            render_mode=work_group.render_mode,
            is_assessable=work_group.is_assessable,
            blank_cells_after=work_group.blank_cells_after,
            blank_cells_rows=work_group.blank_cells_rows,
        )

    def get_orphan_variant_refs(
        self,
        variant_ids: List[str],
    ) -> List[OrphanVariantRef]:
        return [
            OrphanVariantRef(
                pk=str(variant.pk),
                variant_type=variant.variant_type,
                total_max_points=variant.total_max_points,
            )
            for variant in Variant.objects.filter(
                pk__in=variant_ids,
                work__isnull=True,
            ).order_by('created_at')
        ]

    def attach_variants_to_work(self, params: AttachVariantsToWorkParams) -> int:
        with transaction.atomic():
            variants = list(
                Variant.objects.select_for_update().filter(
                    pk__in=params.variant_ids,
                    work__isnull=True,
                ).order_by('created_at')
            )
            variant_by_id = {str(variant.pk): variant for variant in variants}
            attached_count = 0
            for number, variant_id in enumerate(params.variant_ids, 1):
                variant = variant_by_id.get(variant_id)
                if not variant:
                    continue
                variant.work_id = params.work_id
                variant.number = number
                variant.work_name_snapshot = params.work_name_snapshot
                variant.max_score_snapshot = params.max_score_snapshot
                variant.save()
                attached_count += 1
        return attached_count

    def get_variant_delete_info(self, variant_id: str) -> Optional[VariantDeleteInfo]:
        variant = Variant.objects.select_related('work').filter(pk=variant_id).first()
        if variant is None:
            return None
        return VariantDeleteInfo(
            task_count=VariantTask.objects.filter(variant_id=variant_id).count(),
            participation_count=EventParticipation.objects.filter(
                variant_id=variant_id,
            ).count(),
            display_name=variant.display_name,
            short_uuid=variant.get_short_uuid(),
            work_id=str(variant.work_id or ''),
            work_name=variant.work.name if variant.work else '',
            total_max_points=variant.total_max_points,
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
            duration=params.duration,
            max_score=params.max_score,
            variant_counter=params.variant_counter,
        )
        return str(work.pk)

    def update_work(self, params: CreateWorkParams) -> bool:
        work = Work.objects.filter(pk=params.work_id).first()
        if work is None:
            return False

        work.name = params.name
        work.work_type = params.work_type
        work.duration = params.duration
        work.max_score = params.max_score
        work.save()
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
        return str(work.pk)

    def replace_work_analog_groups(
        self,
        work_id: str,
        specs: List[WorkSpecificationRowParams],
    ) -> bool:
        if not Work.objects.filter(pk=work_id).exists():
            return False

        with transaction.atomic():
            WorkAnalogGroup.objects.filter(work_id=work_id).delete()
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
        return True

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
            bank_role = (
                TASK_BANK_ROLE_REMEDIAL
                if params.variant_type == 'remedial'
                else TASK_BANK_ROLE_CONTROL
            )
            VariantTask.objects.create(
                variant=variant,
                task=task,
                order=order,
                weight=points,
                max_points=points,
                bank_role=bank_role,
            )

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
                    order=order,
                )

        return CreatedWorkVariantRef(
            work_id=str(work.pk),
            variant_id=str(variant.pk),
            tasks_count=len(ordered_tasks),
        )

    def _count_available_group_tasks(self, work_group) -> int:
        queryset = TaskGroup.objects.filter(group=work_group.analog_group)
        if work_group.bank_role_filter != TASK_BANK_ROLE_ANY:
            queryset = queryset.filter(bank_role=work_group.bank_role_filter)
        return queryset.count()
