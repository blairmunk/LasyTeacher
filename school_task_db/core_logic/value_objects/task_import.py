"""Task import modes shared by application and infrastructure layers."""

TASK_IMPORT_MODE_STRICT = 'strict'
TASK_IMPORT_MODE_UPDATE = 'update'
TASK_IMPORT_MODE_SKIP = 'skip'

TASK_IMPORT_MODES = (
    TASK_IMPORT_MODE_STRICT,
    TASK_IMPORT_MODE_UPDATE,
    TASK_IMPORT_MODE_SKIP,
)


def validate_task_import_mode(mode: str) -> str:
    if mode not in TASK_IMPORT_MODES:
        available = ', '.join(TASK_IMPORT_MODES)
        raise ValueError(
            f'Неверный режим импорта: {mode}. Доступны: {available}',
        )
    return mode
