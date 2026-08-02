"""Django implementation of the work repository."""

from typing import List, Optional, Set

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Q, Sum

from core_logic.entities.work import (
    OrphanVariantRef,
    OrphanVariantListItem,
    OrphanVariantStudentRef,
    RemedialMarkRef,
    RemedialContentBlockRow,
    RemedialOriginalTaskSource,
    RemedialSheetSource,
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
    VariantGenerationGroupSource,
    VariantGenerationWork,
    VariantListItem,
    VariantListStudentRef,
    VariantListWorkRef,
    WorkDetailAnalogGroup,
    WorkDetailContentBlock,
    WorkDetailSpecGroup,
    WorkDetailVariant,
    WorkDetailWork,
    WorkDocumentRef,
    WorkListItem,
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
from core_logic.interfaces.remedial_source_repo import (
    IRemedialSourceRepository,
)
from core_logic.interfaces.variant_lifecycle_repo import (
    IVariantLifecycleRepository,
)
from core_logic.interfaces.variant_read_repo import IVariantReadRepository
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
)
from core_logic.interfaces.work_read_repo import IWorkReadRepository
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from events.models import EventParticipation
from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
    task_content_snapshot_from_mapping,
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


def _personal_student(variant):
    if variant.assigned_student:
        return variant.assigned_student
    if variant.source_participation:
        return variant.source_participation.student
    return None


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
    IWorkReadRepository,
    IWorkDocumentRepository,
    IWorkVariantGenerationRepository,
    IOrphanVariantRepository,
    IVariantLifecycleRepository,
    IVariantReadRepository,
    IRemedialSourceRepository,
):
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
                display_name=_variant_display_name(variant),
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

    def get_work_document_ref(self, work_id: str):
        work = Work.objects.filter(pk=work_id).only(
            'pk',
            'name',
            'work_type',
        ).first()
        if work is None:
            return None
        return WorkDocumentRef(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
        )

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
            variant_count=Variant.objects.filter(work_id=work_id).count(),
            created_at=work.created_at,
            updated_at=work.updated_at,
        )

    def get_detail_variants(self, work_id: str):
        result = []
        variants = Variant.objects.filter(
            work_id=work_id,
        ).select_related(
            'assigned_student',
            'source_participation__student',
        ).annotate(
            task_count_value=Count('varianttask'),
            total_max_points_value=Sum('varianttask__max_points'),
        )
        for variant in variants:
            personal_student = _personal_student(variant)
            result.append(
                WorkDetailVariant(
                    pk=str(variant.pk),
                    number=variant.number,
                    short_uuid=variant.get_short_uuid(),
                    task_count=variant.task_count_value,
                    total_max_points=variant.total_max_points_value or 0,
                    created_at=variant.created_at,
                    variant_type=variant.variant_type,
                    has_personal_student=bool(personal_student),
                    personal_student_name=(
                        personal_student.get_short_name()
                        if personal_student
                        else ''
                    ),
                )
            )
        return result

    def get_detail_analog_groups(self, work_id: str):
        return [
            self._build_work_detail_spec_group(work_group)
            for work_group in WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        ]

    def get_detail_content_blocks(self, work_id: str):
        return [
            WorkDetailContentBlock(
                pk=str(block.pk),
                content_type=block.content_type,
                order=block.order,
                title=block.title,
                body=block.body,
                topic_ids=tuple(
                    str(topic.pk)
                    for topic in block.topics.all()
                ),
                include_subtopics=block.include_subtopics,
            )
            for block in WorkContentBlock.objects.filter(
                work_id=work_id,
            ).prefetch_related('topics').order_by('order', 'pk')
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
            selection_id=str(work_group.pk),
            bank_role_filter=work_group.bank_role_filter,
            render_mode=work_group.render_mode,
            is_assessable=work_group.is_assessable,
            blank_cells_after=work_group.blank_cells_after,
            blank_cells_rows=work_group.blank_cells_rows,
            task_bank_roles=self._task_bank_roles(
                work_group.analog_group_id,
            ),
        )

    def get_variant_detail(self, variant_id: str):
        variant = Variant.objects.select_related(
            'work',
            'assigned_student',
            'source_work',
            'source_participation__student',
        ).filter(pk=variant_id).first()
        if variant is None:
            return None
        personal_student = _personal_student(variant)

        return VariantDetailVariant(
            pk=str(variant.pk),
            number=variant.number,
            display_name=_variant_display_name(variant),
            short_uuid=variant.get_short_uuid(),
            medium_uuid=variant.get_medium_uuid(),
            variant_type=variant.variant_type,
            variant_type_display=variant.get_variant_type_display(),
            display_duration=variant.duration_snapshot,
            display_max_score=variant.max_score_snapshot,
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
                    pk=str(personal_student.pk),
                    full_name=personal_student.get_full_name(),
                    short_name=personal_student.get_short_name(),
                )
                if personal_student
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
        ).order_by('order')

        result = []
        for variant_task in variant_tasks:
            task = task_content_snapshot_from_mapping(
                variant_task.task_snapshot,
            )
            result.append(VariantDetailTaskRow(
                task=VariantDetailTask(
                    pk=task.task_id,
                    id=task.task_id,
                    topic=task.topic_name,
                    text=task.text,
                    answer=task.answer,
                    task_type_display=task.task_type_display,
                    difficulty=task.difficulty,
                    short_uuid=task.task_id[-4:].upper(),
                    images=[
                        VariantDetailImage(
                            caption=image.caption,
                            position=image.position,
                            safe_url=self._snapshot_image_url(
                                image.file_name,
                            ),
                            css_class=TaskImagePresentationService.css_class(
                                image.position,
                            ),
                        )
                        for image in task.images
                    ],
                ),
                order=variant_task.order,
                max_points=variant_task.max_points,
                bank_role=variant_task.bank_role,
                render_mode=variant_task.render_mode,
                is_assessable=variant_task.is_assessable,
                blank_cells_after=variant_task.blank_cells_after,
                blank_cells_rows=variant_task.blank_cells_rows,
            ))
        return result

    def get_variant_total_max_points(self, variant_id: str) -> int:
        aggregate = VariantTask.objects.filter(
            variant_id=variant_id,
        ).aggregate(total=Sum('max_points'))
        return aggregate['total'] or 0

    def get_variant_type(self, variant_id: str):
        return (
            Variant.objects.filter(pk=variant_id)
            .values_list('variant_type', flat=True)
            .first()
        )

    def get_remedial_sheet_source(
        self,
        variant_id: str,
    ) -> Optional[RemedialSheetSource]:
        variant = Variant.objects.select_related(
            'assigned_student',
            'source_work',
            'source_attempt_snapshot',
            'source_participation__event__work',
            'source_participation__student',
            'source_participation__variant',
            'work',
        ).filter(pk=variant_id).first()
        if variant is None:
            return None
        original_ep = variant.source_participation
        attempt = variant.source_attempt_snapshot
        student = (
            original_ep.student
            if original_ep is not None
            else variant.assigned_student
        )
        source_work = (
            original_ep.event.work
            if original_ep is not None
            else variant.source_work
        )
        student_ref = (
            VariantDetailStudentRef(
                pk=str(student.pk),
                full_name=student.get_full_name(),
                short_name=student.get_short_name(),
            )
            if student
            else (
                VariantDetailStudentRef(
                    pk=attempt.student_id_snapshot,
                    full_name=attempt.student_name_snapshot,
                    short_name=attempt.student_name_snapshot,
                )
                if attempt
                else None
            )
        )
        source_work_ref = (
            VariantDetailRef(
                pk=str(source_work.pk),
                name=source_work.name,
            )
            if source_work
            else (
                VariantDetailRef(
                    pk=attempt.work_id_snapshot,
                    name=attempt.work_name_snapshot,
                )
                if attempt
                else None
            )
        )
        mark_ref = None
        task_scores = {}
        original_tasks = []

        if attempt:
            mark_ref = RemedialMarkRef(
                score=attempt.score,
                points=attempt.points,
                max_points=attempt.max_points,
            )
            task_scores = dict(attempt.task_scores_snapshot or {})
            for task_result in attempt.task_results.select_related(
                'variant_task',
            ).order_by('order_snapshot', 'pk'):
                variant_task = task_result.variant_task
                task = task_content_snapshot_from_mapping(
                    variant_task.task_snapshot,
                )
                task_group = TaskGroup.objects.filter(
                    task_id=task.task_id,
                ).first()
                original_tasks.append(
                    RemedialOriginalTaskSource(
                        task=self._remedial_task_ref(task),
                        variant_task_id=str(variant_task.pk),
                        order=task_result.order_snapshot,
                        group_name=(
                            task_group.group.name if task_group else ''
                        ),
                    )
                )

        new_tasks = VariantTask.objects.filter(
            variant=variant,
        ).order_by('order')

        return RemedialSheetSource(
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
            student=student_ref,
            source_work=source_work_ref,
            mark=mark_ref,
            task_scores=task_scores,
            original_tasks=original_tasks,
            new_tasks=[
                RemedialTrainingTaskRow(
                    pk=str(variant_task.pk),
                    task_id=str(variant_task.task_id),
                    task=self._remedial_task_ref(
                        task_content_snapshot_from_mapping(
                            variant_task.task_snapshot,
                        ),
                    ),
                    order=variant_task.order,
                    max_points=variant_task.max_points,
                    source_selection_id=(
                        str(variant_task.source_selection_id)
                        if variant_task.source_selection_id
                        else ''
                    ),
                    content_order=variant_task.content_order,
                    bank_role=variant_task.bank_role,
                    render_mode=variant_task.render_mode,
                    is_assessable=variant_task.is_assessable,
                    blank_cells_after=variant_task.blank_cells_after,
                    blank_cells_rows=variant_task.blank_cells_rows,
                )
                for variant_task in new_tasks
            ],
            content_blocks=[
                RemedialContentBlockRow(
                    pk=str(block.pk),
                    source_content_id=block.source_content_id,
                    content_type=block.content_type,
                    order=block.order,
                    title=block.title,
                    content=block.content,
                )
                for block in variant.content_block_snapshots.order_by(
                    'order',
                    'pk',
                )
            ],
        )

    @staticmethod
    def _remedial_task_ref(task):
        return RemedialTaskRef(
            pk=task.task_id,
            text=task.text,
            answer=task.answer,
            short_solution=task.short_solution,
            full_solution=task.full_solution,
            hint=task.hint,
            instruction=task.instruction,
            task_type=task.task_type,
            difficulty=task.difficulty,
            topic=task.topic_name,
            subtopic=task.subtopic_name,
            source=task.source_name,
            source_detail=task.source_detail,
        )

    @staticmethod
    def _snapshot_image_url(file_name):
        if not file_name:
            return None
        try:
            return default_storage.url(file_name)
        except ValueError:
            return None

    def get_work_personal_remedial_variant_ids(
        self,
        work_id: str,
    ) -> List[str]:
        return [
            str(variant_id)
            for variant_id in Variant.objects.filter(
                work_id=work_id,
                variant_type='remedial',
            ).filter(
                Q(assigned_student_id__isnull=False)
                | Q(source_participation_id__isnull=False),
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

            work_id = self.create_work(
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

    def get_event_variant_task_ids(
        self,
        event_id: str,
        student_id: str,
    ) -> Set[str]:
        participation = EventParticipation.objects.filter(
            event_id=event_id,
            student_id=student_id,
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
            work_id = self.create_work(params.work)
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

    def replace_work_analog_groups(
        self,
        work_id: str,
        specs: List[WorkTaskSelectionParams],
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

    def replace_work_content_plan(
        self,
        work_id: str,
        specs: List[WorkTaskSelectionParams],
        content_blocks: List[WorkContentBlockParams],
    ) -> bool:
        if not Work.objects.filter(pk=work_id).exists():
            return False

        with transaction.atomic():
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
        return True

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
