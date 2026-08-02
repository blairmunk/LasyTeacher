"""Test factory enforcing the generated-variant snapshot invariant."""

from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from infrastructure.repositories.django_attempt_snapshot_repo import (
    DjangoAttemptSnapshotRepository,
)
from events.models import AttemptSnapshot
from tasks.models import Task
from works.models import VariantTask


def create_variant_task(**kwargs):
    task = kwargs.get('task')
    if task is None:
        task = Task.objects.get(pk=kwargs['task_id'])
    kwargs.setdefault(
        'task_snapshot',
        build_task_content_snapshots([task])[str(task.pk)].to_mapping(),
    )
    return VariantTask.objects.create(**kwargs)


def capture_attempt_snapshot(mark):
    """Capture and return the immutable checked-attempt revision for a mark."""
    ref = DjangoAttemptSnapshotRepository().capture_mark(str(mark.pk))
    return AttemptSnapshot.objects.get(pk=ref.pk)
