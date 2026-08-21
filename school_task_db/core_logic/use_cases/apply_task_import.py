"""Apply a validated task-bank payload through a persistence session."""

from core_logic.entities.task_import import (
    TaskImportRequest,
    TaskImportRunSummary,
)
from core_logic.interfaces.task_import import ITaskImportWriteSession
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.value_objects.task_import import validate_task_import_mode


class ApplyTaskImportUseCase:
    """Own the write order and transaction boundary of a task import."""

    def __init__(
        self,
        write_session: ITaskImportWriteSession,
        transaction_manager: ITransactionManager,
    ):
        self.write_session = write_session
        self.transaction_manager = transaction_manager

    def execute(self, request: TaskImportRequest) -> TaskImportRunSummary:
        validate_task_import_mode(request.mode)
        data = request.data

        with self.transaction_manager.atomic():
            if 'sources' in data:
                self.write_session.import_sources(data['sources'])
            if 'analog_groups' in data:
                self.write_session.import_groups(data['analog_groups'])
            if request.create_missing and 'topics' in data:
                self.write_session.import_topics(data['topics'])
            if 'tasks' in data:
                self.write_session.import_tasks(data['tasks'])

            tasks = data.get('tasks', [])
            self.write_session.import_task_group_relations(tasks)

            if 'task_images' in data:
                self.write_session.import_images(data['task_images'])

        return self.write_session.summary()
