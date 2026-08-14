"""Django command adapter for variant detach and deletion workflows."""

from typing import Sequence

from django.db import transaction
from django.db.models.deletion import ProtectedError

from core_logic.entities.work import VariantDeletionOutcome
from core_logic.interfaces.variant_lifecycle_command_repo import (
    IVariantLifecycleCommandRepository,
)
from events.models import EventParticipation
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

    @transaction.atomic
    def delete_variant_if_unreferenced(
        self,
        variant_id: str,
    ) -> VariantDeletionOutcome:
        variant = Variant.objects.select_for_update().filter(
            pk=variant_id,
        ).first()
        if variant is None:
            return VariantDeletionOutcome(status='not_found')

        participations = EventParticipation.objects.filter(
            variant_id=variant_id,
        )
        participation_count = participations.count()
        if participation_count:
            return VariantDeletionOutcome(
                status='blocked_has_participations',
                participation_count=participation_count,
            )

        work_id = str(variant.work_id or '')
        try:
            with transaction.atomic():
                variant.delete()
        except ProtectedError:
            return VariantDeletionOutcome(
                status='blocked_has_participations',
                participation_count=participations.count(),
            )
        return VariantDeletionOutcome(status='deleted', work_id=work_id)

    def bulk_delete_work_variants(
        self,
        work_id: str,
        variant_ids: Sequence[str],
    ) -> int:
        return Variant.objects.filter(
            pk__in=variant_ids,
            work_id=work_id,
        ).delete()[0]
