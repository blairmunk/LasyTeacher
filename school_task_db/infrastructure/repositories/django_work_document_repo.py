"""Django read adapter for regular work document sources."""

from typing import List, Optional

from django.db.models import Prefetch

from core_logic.entities.work import (
    WorkDocumentRef,
)
from core_logic.interfaces.work_document_repo import IWorkDocumentRepository
from core_logic.entities.work_document import (
    WorkDocumentContentBlockSource,
    WorkDocumentScoreSpecRow,
    WorkDocumentSource,
    WorkDocumentTaskSource,
    WorkDocumentVariantSource,
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
                    page_break_after=variant_task.page_break_after,
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
