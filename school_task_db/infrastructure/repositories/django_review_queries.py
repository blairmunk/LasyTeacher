"""Shared Django queries used by review read adapters."""

from django.db.models import Count

from works.models import VariantTask


def variant_task_counts(variant_ids) -> dict:
    variant_ids = [variant_id for variant_id in variant_ids if variant_id]
    if not variant_ids:
        return {}

    rows = VariantTask.objects.filter(
        variant_id__in=variant_ids,
    ).values('variant_id').annotate(total=Count('id'))
    return {row['variant_id']: row['total'] for row in rows}
