"""Shared Django queries for task classification controls."""

from django.db.models import Q

from codifier.models import ContentEntry, Requirement


def task_classification_querysets(
    *,
    topic=None,
    current_content_ids=(),
    current_requirement_ids=(),
):
    content_entries = ContentEntry.objects.all()
    requirements = Requirement.objects.all()
    if topic is not None:
        content_entries = content_entries.filter(
            codifier__subject=topic.subject,
        )
        requirements = requirements.filter(
            codifier__subject=topic.subject,
        )

    content_entries = content_entries.filter(
        Q(codifier__is_active=True) | Q(pk__in=current_content_ids),
    ).select_related('codifier').order_by(
        '-codifier__year',
        'codifier__exam_type',
        'code',
    )
    requirements = requirements.filter(
        Q(codifier__is_active=True) | Q(pk__in=current_requirement_ids),
    ).select_related('codifier').order_by(
        '-codifier__year',
        'codifier__exam_type',
        'code',
    )
    return content_entries, requirements
