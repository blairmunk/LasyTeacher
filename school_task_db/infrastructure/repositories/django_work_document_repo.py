"""Django read adapter for work and remedial document sources."""

from typing import List, Optional

from django.db.models import Prefetch, Q

from core_logic.entities.work import (
    RemedialContentBlockRow,
    RemedialMarkRef,
    RemedialOriginalTaskSource,
    RemedialSheetSource,
    RemedialTaskRef,
    RemedialTrainingTaskRow,
    RemedialVariantRef,
    VariantDetailRef,
    VariantDetailStudentRef,
    WorkDocumentRef,
)
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_from_mapping,
)
from core_logic.entities.work_document import (
    WorkDocumentContentBlockSource,
    WorkDocumentScoreSpecRow,
    WorkDocumentSource,
    WorkDocumentTaskSource,
    WorkDocumentVariantSource,
)
from infrastructure.services.django_captured_task_result_queries import (
    captured_task_result_snapshot,
)
from works.models import (
    Variant,
    VariantContentBlockSnapshot,
    VariantTask,
    Work,
    WorkAnalogGroup,
)


class DjangoWorkDocumentRepository(IWorkDocumentRepository):
    def get_work_document_source(
        self,
        work_id: str,
    ) -> Optional[WorkDocumentSource]:
        variants = Variant.objects.order_by('number', 'pk').prefetch_related(
            Prefetch(
                'varianttask_set',
                queryset=VariantTask.objects.order_by('order', 'pk'),
                to_attr='document_tasks',
            ),
            Prefetch(
                'content_block_snapshots',
                queryset=VariantContentBlockSnapshot.objects.order_by(
                    'order',
                    'pk',
                ),
                to_attr='document_content_blocks',
            ),
        )
        work = Work.objects.prefetch_related(
            Prefetch(
                'workanaloggroup_set',
                queryset=WorkAnalogGroup.objects.order_by('order', 'pk'),
                to_attr='document_score_spec_rows',
            ),
            Prefetch(
                'variant_set',
                queryset=variants,
                to_attr='document_variants',
            ),
        ).filter(pk=work_id).first()
        if work is None:
            return None

        return WorkDocumentSource(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            duration=work.duration,
            max_score=work.max_score,
            score_spec_rows=tuple(
                WorkDocumentScoreSpecRow(
                    pk=str(row.pk),
                    count=row.count,
                    weight=row.weight,
                    is_assessable=row.is_assessable,
                )
                for row in work.document_score_spec_rows
            ),
            variants=tuple(
                self._work_document_variant_source(variant)
                for variant in work.document_variants
            ),
        )

    @staticmethod
    def _work_document_variant_source(variant):
        return WorkDocumentVariantSource(
            pk=str(variant.pk),
            number=variant.number,
            max_score_snapshot=variant.max_score_snapshot,
            duration_snapshot=variant.duration_snapshot,
            tasks=tuple(
                WorkDocumentTaskSource(
                    pk=str(variant_task.pk),
                    task_id=str(variant_task.task_id),
                    task_snapshot=variant_task.task_snapshot,
                    order=variant_task.order,
                    max_points=variant_task.max_points,
                    source_selection_id=variant_task.source_selection_id,
                    content_order=variant_task.content_order,
                    bank_role=variant_task.bank_role,
                    render_mode=variant_task.render_mode,
                    is_assessable=variant_task.is_assessable,
                    blank_cells_after=variant_task.blank_cells_after,
                    blank_cells_rows=variant_task.blank_cells_rows,
                )
                for variant_task in variant.document_tasks
            ),
            content_blocks=tuple(
                WorkDocumentContentBlockSource(
                    pk=str(block.pk),
                    source_content_id=block.source_content_id,
                    content_type=block.content_type,
                    order=block.order,
                    title=block.title,
                    content=block.content,
                )
                for block in variant.document_content_blocks
            ),
        )

    def get_work_document_ref(self, work_id: str):
        work = Work.objects.filter(pk=work_id).only(
            'pk',
            'name',
            'work_type',
            'assessment_mode',
        ).first()
        if work is None:
            return None
        return WorkDocumentRef(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            assessment_mode=work.assessment_mode,
        )

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
        original_tasks = []

        if attempt:
            mark_ref = RemedialMarkRef(
                score=attempt.score,
                points=attempt.points,
                max_points=attempt.max_points,
            )
            for task_result in attempt.task_results.order_by(
                'order_snapshot',
                'pk',
            ):
                captured = captured_task_result_snapshot(task_result)
                if captured is None or not captured.is_assessable:
                    continue
                original_tasks.append(
                    RemedialOriginalTaskSource(
                        task=self._remedial_task_ref(captured.task),
                        order=captured.order,
                        group_name=captured.source_selection_name,
                        points=captured.points,
                        max_points=captured.max_points,
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
