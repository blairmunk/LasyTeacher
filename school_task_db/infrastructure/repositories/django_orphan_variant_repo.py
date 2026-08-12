"""Django repository for orphan variant workflows."""

from typing import List, Optional

from django.db import transaction
from django.db.models import Count, Sum

from core_logic.entities.work import (
    OrphanVariantListItem,
    OrphanVariantRef,
    OrphanVariantStudentRef,
)
from core_logic.entities.orphan_variant_commands import (
    CreatedWorkFromOrphanVariantsRef,
    CreateWorkFromOrphanVariantsParams,
)
from core_logic.interfaces.orphan_variant_repo import (
    IOrphanVariantRepository,
)
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from works.models import Variant, Work


def _variant_display_name(variant: Variant) -> str:
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


class DjangoOrphanVariantRepository(IOrphanVariantRepository):
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

            work = Work.objects.create(
                name=params.name,
                work_type=params.work_type,
                max_score=params.max_score,
                variant_counter=len(variants),
            )
            variant_by_id = {str(variant.pk): variant for variant in variants}
            for number, variant_id in enumerate(params.variant_ids, 1):
                variant = variant_by_id[variant_id]
                variant.work = work
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
            work_id=str(work.pk),
            variant_count=len(variants),
        )
