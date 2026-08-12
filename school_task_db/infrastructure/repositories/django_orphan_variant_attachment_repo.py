"""Django adapter for attaching orphan variants to a new work."""

from typing import List, Optional

from django.db import transaction
from django.db.models import Sum

from core_logic.entities.orphan_variant_commands import (
    CreatedWorkFromOrphanVariantsRef,
    CreateWorkFromOrphanVariantsParams,
)
from core_logic.entities.work import OrphanVariantRef
from core_logic.interfaces.orphan_variant_attachment_repo import (
    IOrphanVariantAttachmentRepository,
)
from works.models import Variant, Work


class DjangoOrphanVariantAttachmentRepository(
    IOrphanVariantAttachmentRepository,
):
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
