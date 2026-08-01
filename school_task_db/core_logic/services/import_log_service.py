"""Pure import log presentation calculations."""


class ImportLogService:
    STATUS_ICONS = {
        'validating': '🔍',
        'importing': '⏳',
        'success': '✅',
        'partial': '⚠️',
        'failed': '❌',
    }

    @staticmethod
    def total_processed(created: int, updated: int, skipped: int) -> int:
        return created + updated + skipped

    @classmethod
    def status_icon(cls, status: str) -> str:
        return cls.STATUS_ICONS.get(status, '❓')

    @staticmethod
    def duration_human(duration_ms: int) -> str:
        if duration_ms < 1000:
            return f'{duration_ms} мс'
        return f'{duration_ms / 1000:.1f} с'

    @staticmethod
    def file_size_human(file_size: int) -> str:
        if file_size < 1024:
            return f'{file_size} Б'
        if file_size < 1024 * 1024:
            return f'{file_size / 1024:.1f} КБ'
        return f'{file_size / 1024 / 1024:.1f} МБ'
