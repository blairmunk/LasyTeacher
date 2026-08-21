"""Version markers for portable task-bank files."""

TASK_TRANSFER_FORMAT_VERSION = '1.5'
SUPPORTED_TASK_TRANSFER_FORMAT_VERSIONS = (
    '1.0',
    '1.1',
    '1.2',
    '1.3',
    '1.4',
    TASK_TRANSFER_FORMAT_VERSION,
)


def task_transfer_format_version(data) -> str:
    if not isinstance(data, dict):
        return ''
    value = data.get('version', data.get('format_version', ''))
    return str(value).strip() if value is not None else ''


def task_transfer_format_error(data) -> str:
    version = task_transfer_format_version(data)
    if not version or version in SUPPORTED_TASK_TRANSFER_FORMAT_VERSIONS:
        return ''
    return (
        f'Неподдерживаемая версия формата заданий: {version}. '
        f'Поддерживаются версии '
        f'{", ".join(SUPPORTED_TASK_TRANSFER_FORMAT_VERSIONS)}'
    )


def task_transfer_format_warning(data) -> str:
    version = task_transfer_format_version(data)
    if not version or version == TASK_TRANSFER_FORMAT_VERSION:
        return ''
    if version not in SUPPORTED_TASK_TRANSFER_FORMAT_VERSIONS:
        return ''
    return (
        f'Файл использует формат {version}; после импорта рекомендуется '
        f'экспортировать его в актуальном формате '
        f'{TASK_TRANSFER_FORMAT_VERSION}'
    )
