"""Django task source import and reference resolution."""

from typing import Any

from tasks.models import Source


class TaskSourceImporter:
    def __init__(self, runtime):
        self.runtime = runtime

    def import_sources(self, sources_data):
        self.runtime._write('📚 Импорт источников...')
        for source_data in sources_data:
            try:
                source = self.resolve(source_data)
                if source:
                    self.runtime.log_info(f'Источник: {source}')
            except Exception as error:
                self.runtime.log_error(
                    f'Ошибка импорта источника: {error}',
                    error,
                )

    def resolve(self, source_data: Any):
        if not source_data:
            return None
        if isinstance(source_data, str):
            return (
                Source.objects.filter(name=source_data).first()
                or Source.objects.filter(short_name=source_data).first()
            )
        if not isinstance(source_data, dict):
            return None

        source = self._find_existing(source_data)
        if source:
            self._update(source, source_data)
            return source
        if not self.runtime.create_missing or not source_data.get('name'):
            return None

        try:
            source = Source.objects.create(
                name=source_data['name'],
                short_name=source_data.get('short_name', ''),
                source_type=source_data.get('source_type', 'other'),
                author=source_data.get('author', ''),
                year=source_data.get('year'),
                url=source_data.get('url', ''),
                isbn=source_data.get('isbn', ''),
                notes=source_data.get('notes', ''),
            )
            self.runtime.log_success(f'Создан источник: {source}')
            return source
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка создания источника: {error}',
                error,
            )
            return None

    @staticmethod
    def _find_existing(source_data):
        short_name = source_data.get('short_name')
        if short_name:
            source = Source.objects.filter(short_name=short_name).first()
            if source:
                return source
        name = source_data.get('name')
        if name:
            return Source.objects.filter(name=name).first()
        return None

    def _update(self, source, source_data):
        if self.runtime.mode != 'update':
            return
        update_fields = []
        for field in (
            'name',
            'short_name',
            'source_type',
            'author',
            'year',
            'url',
            'isbn',
            'notes',
        ):
            if field in source_data:
                setattr(source, field, source_data[field])
                update_fields.append(field)
        if update_fields:
            source.save(update_fields=update_fields)
