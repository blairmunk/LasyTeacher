"""Test factory enforcing the generated-variant snapshot invariant."""

from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
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
