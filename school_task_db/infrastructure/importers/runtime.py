"""Per-operation state for Django task-bank imports."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from core_logic.value_objects.task_import import (
    TASK_IMPORT_ACTION_SKIP,
    task_import_action,
)
from infrastructure.repositories.django_uuid_lookup import (
    get_unambiguous_by_uuid,
)


@dataclass(frozen=True)
class TaskImportIssue:
    message: str
    exception: str = ''
    context: Dict[str, Any] = field(default_factory=dict)


class TaskImportStatistics:
    def __init__(self):
        self.created_by_type = {}
        self.updated_by_type = {}
        self.skipped_by_type = {}
        self._recorded_operations = set()
        self.errors = []
        self.warnings = []

    def add_warning(self, message: str, context: Optional[Dict] = None):
        self.warnings.append(TaskImportIssue(message, context=context or {}))

    def add_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict] = None,
    ):
        self.errors.append(TaskImportIssue(
            message=message,
            exception=str(exception) if exception else '',
            context=context or {},
        ))

    def record_created(self, object_type: str, object_id=''):
        self._record('created', object_type, object_id)

    def record_updated(self, object_type: str, object_id=''):
        self._record('updated', object_type, object_id)

    def record_skipped(self, object_type: str, object_id=''):
        self._record('skipped', object_type, object_id)

    def _record(self, action: str, object_type: str, object_id):
        operation_key = (action, object_type, str(object_id))
        if object_id and operation_key in self._recorded_operations:
            return
        if object_id:
            self._recorded_operations.add(operation_key)
        counts = getattr(self, f'{action}_by_type')
        counts[object_type] = counts.get(object_type, 0) + 1


class TaskImportRegistry:
    """ORM identity map scoped to one import transaction."""

    def __init__(self):
        self._topics = {}
        self._subtopics = {}
        self._groups = {}
        self._sources = {}
        self._tasks = {}
        self._task_actions = {}

    def remember_topic(self, object_id: str, topic):
        self._topics[object_id] = topic

    def topic(self, object_id: str):
        return self._topics.get(object_id)

    def remember_subtopic(self, object_id: str, subtopic):
        self._subtopics[object_id] = subtopic

    def subtopic(self, object_id: str):
        return self._subtopics.get(object_id)

    def remember_group(self, object_id: str, group):
        self._groups[object_id] = group

    def group(self, object_id: str):
        return self._groups.get(object_id)

    def remember_source(self, object_id: str, source):
        self._sources[object_id] = source

    def source(self, object_id: str):
        return self._sources.get(object_id)

    def remember_task(self, object_id: str, task, *, action: str = ''):
        self._tasks[object_id] = task
        if action:
            self._task_actions[object_id] = action

    def task(self, object_id: str):
        return self._tasks.get(object_id)

    def task_action(self, object_id: str) -> str:
        return self._task_actions.get(object_id, '')

    def counts(self) -> Dict[str, int]:
        return {
            'topics': len(self._topics),
            'subtopics': len(self._subtopics),
            'groups': len(self._groups),
            'sources': len(self._sources),
            'tasks': len(self._tasks),
        }


class TaskImportRuntime:
    def __init__(
        self,
        *,
        mode: str,
        verbose: bool,
        create_missing: bool,
        output: Optional[Callable[[str], None]],
    ):
        self.mode = mode
        self.verbose = verbose
        self.create_missing = create_missing
        self.output = output
        self.stats = TaskImportStatistics()
        self._cache = {}

    def write(self, message: str = ''):
        if self.output is not None:
            self.output(message)
        else:
            print(message)

    def log_info(self, message: str, indent: int = 0):
        if self.verbose:
            self.write(f'{"  " * indent}{message}')

    def log_warning(self, message: str, context: Optional[Dict] = None):
        self.write(f'  ⚠️ {message}')
        self.stats.add_warning(message, context)

    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict] = None,
    ):
        self.write(f'  ❌ {message}')
        if exception and self.verbose:
            self.write(f'     Детали: {exception}')
        self.stats.add_error(message, exception, context)

    def log_success(self, message: str):
        if self.verbose:
            self.write(f'  ✅ {message}')

    def generate_uuid_if_missing(
        self,
        data: Dict[str, Any],
        field_name: str = 'id',
    ) -> str:
        if field_name not in data or not data[field_name]:
            data[field_name] = str(uuid4())
            self.log_info(f'Генерируем UUID: {data[field_name][-8:]}')
        return data[field_name]

    def get_by_uuid(self, model_class, uuid_str: str):
        cache_key = f'{model_class.__name__}:{uuid_str}'
        if cache_key in self._cache:
            return self._cache[cache_key]
        try:
            obj = get_unambiguous_by_uuid(model_class, uuid_str)
        except Exception as error:
            self.log_error(
                f'Ошибка поиска {model_class.__name__} с UUID '
                f'{uuid_str[-8:]}: {error}',
            )
            return None
        if obj is not None:
            self._cache[cache_key] = obj
        return obj

    def object_action(
        self,
        existing_obj,
        data: Dict[str, Any],
        object_type: str,
    ) -> str:
        action = task_import_action(
            self.mode,
            exists=existing_obj is not None,
            object_id=data.get('id', 'unknown'),
        )
        if action == TASK_IMPORT_ACTION_SKIP:
            self.stats.record_skipped(object_type, existing_obj.pk)
        return action
