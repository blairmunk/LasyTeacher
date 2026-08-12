"""Django command adapter for variant detach and deletion workflows."""

from typing import List

from core_logic.interfaces.variant_lifecycle_command_repo import (
    IVariantLifecycleCommandRepository,
)
from works.models import Variant


class DjangoVariantLifecycleCommandRepository(
    IVariantLifecycleCommandRepository,
):
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
