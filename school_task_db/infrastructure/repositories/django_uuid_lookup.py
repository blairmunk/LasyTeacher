"""Shared Django queries for UUID fragments."""

from django.db.models import CharField, Value
from django.db.models.functions import Cast, Replace

from core_logic.value_objects.short_uuid import (
    is_uuid_search_fragment,
    normalize_uuid_fragment,
)


def filter_by_uuid_suffix(model_class, value):
    """Return objects whose own UUID ends with a valid fragment."""
    fragment = normalize_uuid_fragment(value)
    if not is_uuid_search_fragment(fragment):
        return model_class.objects.none()
    return model_class.objects.annotate(
        uuid_search_value=Replace(
            Cast('id', output_field=CharField()),
            Value('-'),
            Value(''),
        ),
    ).filter(uuid_search_value__iendswith=fragment)


def get_unambiguous_by_uuid(model_class, value):
    """Return one exact/suffix UUID match, or None for zero/many matches."""
    matching_ids = tuple(
        filter_by_uuid_suffix(model_class, value)
        .values_list('pk', flat=True)[:2]
    )
    if len(matching_ids) != 1:
        return None
    return model_class.objects.filter(pk=matching_ids[0]).first()
