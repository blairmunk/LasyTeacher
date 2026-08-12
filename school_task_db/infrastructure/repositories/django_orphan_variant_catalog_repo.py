"""Django read adapter for the orphan variant catalog."""

from django.db.models import Count, Sum

from core_logic.entities.work import (
    OrphanVariantListItem,
    OrphanVariantStudentRef,
)
from core_logic.interfaces.orphan_variant_catalog_repo import (
    IOrphanVariantCatalogRepository,
)
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from works.models import Variant


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


class DjangoOrphanVariantCatalogRepository(
    IOrphanVariantCatalogRepository,
):
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
