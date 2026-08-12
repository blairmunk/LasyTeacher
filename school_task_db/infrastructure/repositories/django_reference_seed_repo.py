"""Django persistence adapter for editable reference catalog seeds."""

from core_logic.entities.reference_seed import (
    ReferenceSeedMutation,
    SimpleReferenceSeedItem,
    SubjectReferenceSeedItem,
)
from core_logic.interfaces.reference_seed_repo import IReferenceSeedRepository
from references.models import SimpleReference, SubjectReference


class DjangoReferenceSeedRepository(IReferenceSeedRepository):
    def seed_simple_reference(
        self,
        item: SimpleReferenceSeedItem,
        replace_existing: bool,
    ) -> ReferenceSeedMutation:
        reference, created = SimpleReference.objects.get_or_create(
            category=item.category,
            defaults={
                'items_text': item.items_text,
                'is_active': item.is_active,
            },
        )
        status = _replace_or_status(
            reference,
            created=created,
            replace_existing=replace_existing,
            items_text=item.items_text,
            is_active=item.is_active,
        )
        return ReferenceSeedMutation(
            reference_type='simple',
            key=(item.category,),
            display_name=reference.get_category_display(),
            status=status,
            items_count=len(reference.get_items_list()),
        )

    def seed_subject_reference(
        self,
        item: SubjectReferenceSeedItem,
        replace_existing: bool,
    ) -> ReferenceSeedMutation:
        reference, created = SubjectReference.objects.get_or_create(
            subject=item.subject,
            grade_level=item.grade_level,
            category=item.category,
            defaults={
                'items_text': item.items_text,
                'is_active': item.is_active,
            },
        )
        status = _replace_or_status(
            reference,
            created=created,
            replace_existing=replace_existing,
            items_text=item.items_text,
            is_active=item.is_active,
        )
        return ReferenceSeedMutation(
            reference_type='subject',
            key=(item.subject, item.grade_level, item.category),
            display_name=str(reference),
            status=status,
            items_count=len(reference.get_items_dict()),
        )


def _replace_or_status(
    reference,
    *,
    created,
    replace_existing,
    items_text,
    is_active,
):
    if created:
        return 'created'
    if not replace_existing:
        return 'skipped'
    reference.items_text = items_text
    reference.is_active = is_active
    reference.save(update_fields=['items_text', 'is_active', 'updated_at'])
    return 'updated'
