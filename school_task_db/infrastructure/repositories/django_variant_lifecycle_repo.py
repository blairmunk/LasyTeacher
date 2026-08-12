"""Django repository for variant detach and deletion workflows."""

from typing import List, Optional

from django.db.models import Sum

from core_logic.entities.work import VariantDeleteInfo
from core_logic.interfaces.variant_lifecycle_command_repo import (
    IVariantLifecycleCommandRepository,
)
from core_logic.interfaces.variant_lifecycle_query_repo import (
    IVariantLifecycleQueryRepository,
)
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from events.models import EventParticipation
from works.models import Variant, VariantTask


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


class DjangoVariantLifecycleRepository(
    IVariantLifecycleQueryRepository,
    IVariantLifecycleCommandRepository,
):
    def get_variant_delete_info(
        self,
        variant_id: str,
    ) -> Optional[VariantDeleteInfo]:
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

    def bulk_delete_work_variants(
        self,
        work_id: str,
        variant_ids: List[str],
    ) -> int:
        return Variant.objects.filter(
            pk__in=variant_ids,
            work_id=work_id,
        ).delete()[0]

    def count_work_variants(self, work_id: str) -> int:
        return Variant.objects.filter(work_id=work_id).count()
