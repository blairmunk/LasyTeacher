"""Task import settings and portable reference values."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_CONTROL,
    validate_task_specific_bank_role,
)

TASK_IMPORT_MODE_STRICT = 'strict'
TASK_IMPORT_MODE_UPDATE = 'update'
TASK_IMPORT_MODE_SKIP = 'skip'

TASK_IMPORT_MODES = (
    TASK_IMPORT_MODE_STRICT,
    TASK_IMPORT_MODE_UPDATE,
    TASK_IMPORT_MODE_SKIP,
)

TASK_IMPORT_MODE_LABELS = {
    TASK_IMPORT_MODE_STRICT: 'Строгий',
    TASK_IMPORT_MODE_UPDATE: 'Обновление',
    TASK_IMPORT_MODE_SKIP: 'Пропуск дубликатов',
}

TASK_IMPORT_ACTION_CREATE = 'create'
TASK_IMPORT_ACTION_UPDATE = 'update'
TASK_IMPORT_ACTION_SKIP = 'skip'


class TaskImportConflictError(ValueError):
    """An imported UUID conflicts with an existing object in strict mode."""


@dataclass(frozen=True)
class TaskGroupImportReference:
    group_id: str
    bank_role: str = TASK_BANK_ROLE_CONTROL


def parse_task_group_import_reference(
    value: Any,
) -> TaskGroupImportReference:
    if isinstance(value, str):
        group_id = value
        bank_role = TASK_BANK_ROLE_CONTROL
    elif isinstance(value, dict):
        group_id = value.get('id') or value.get('group_id') or ''
        bank_role = value.get('bank_role', TASK_BANK_ROLE_CONTROL)
    else:
        raise ValueError(
            'связь с группой должна быть UUID-строкой '
            'или объектом',
        )

    if not group_id:
        raise ValueError('у связи с группой отсутствует id')
    try:
        normalized_group_id = str(UUID(str(group_id)))
    except (TypeError, ValueError) as error:
        raise ValueError(
            f'у связи с группой некорректный UUID '
            f'"{group_id}"',
        ) from error

    validate_task_specific_bank_role(bank_role)
    return TaskGroupImportReference(
        group_id=normalized_group_id,
        bank_role=bank_role,
    )


def validate_task_import_mode(mode: str) -> str:
    if mode not in TASK_IMPORT_MODES:
        available = ', '.join(TASK_IMPORT_MODES)
        raise ValueError(
            f'Неверный режим импорта: {mode}. Доступны: {available}',
        )
    return mode


def task_import_action(
    mode: str,
    *,
    exists: bool,
    object_id: str = '',
) -> str:
    validate_task_import_mode(mode)
    if not exists:
        return TASK_IMPORT_ACTION_CREATE
    if mode == TASK_IMPORT_MODE_UPDATE:
        return TASK_IMPORT_ACTION_UPDATE
    if mode == TASK_IMPORT_MODE_SKIP:
        return TASK_IMPORT_ACTION_SKIP
    suffix = str(object_id or 'unknown')[-8:]
    raise TaskImportConflictError(
        f'Объект с UUID {suffix} уже существует '
        'в strict режиме',
    )


def task_import_mode_label(mode: str) -> str:
    validate_task_import_mode(mode)
    return TASK_IMPORT_MODE_LABELS[mode]
