"""Django command adapter for the task lifecycle."""

from core_logic.interfaces.task_lifecycle_command_repo import (
    ITaskLifecycleCommandRepository,
)
from tasks.models import Task


class DjangoTaskLifecycleCommandRepository(
    ITaskLifecycleCommandRepository,
):
    def delete_task(self, task_id: str) -> int:
        tasks = Task.objects.filter(pk=task_id)
        deleted_count = tasks.count()
        tasks.delete()
        return deleted_count
