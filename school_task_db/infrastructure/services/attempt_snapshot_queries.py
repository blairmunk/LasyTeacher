"""Shared Django queries for versioned checked attempts."""

from django.db.models import OuterRef, Prefetch, Subquery

from events.models import AttemptSnapshot, AttemptTaskSnapshot


def latest_attempts_by_participation(
    participation_ids,
    *,
    include_task_results=True,
):
    """Return the latest captured attempt for every requested participation."""
    participation_ids = tuple(participation_ids)
    if not participation_ids:
        return {}

    latest_revision = AttemptSnapshot.objects.filter(
        participation_id=OuterRef('participation_id'),
    ).order_by('-revision').values('revision')[:1]
    attempts = AttemptSnapshot.objects.filter(
        participation_id__in=participation_ids,
        revision=Subquery(latest_revision),
    )
    if include_task_results:
        attempts = attempts.prefetch_related(
            Prefetch(
                'task_results',
                queryset=AttemptTaskSnapshot.objects.select_related(
                    'variant_task',
                ).order_by('order_snapshot', 'pk'),
                to_attr='captured_task_results',
            ),
        )
    return {
        attempt.participation_id: attempt
        for attempt in attempts
    }
