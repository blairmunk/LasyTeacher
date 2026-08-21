"""Django task source import and reference resolution."""

from typing import Any

from tasks.models import Source


class TaskSourceImporter:
    def __init__(self, runtime):
        self.runtime = runtime

    def import_sources(self, sources_data):
        self.runtime.write('📚 Импорт источников...')
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
        if not isinstance(source_data, dict):
            return None

        source = self._find_existing(source_data)
        if source:
            self._update(source, source_data)
            return source
        source_id = source_data.get('id') or source_data.get('uuid')
        if (
            not self.runtime.create_missing
            or not source_id
            or not source_data.get('name')
        ):
            return None

        try:
            create_values = dict(
                name=source_data['name'],
                short_name=source_data.get('short_name', ''),
                source_type=source_data.get('source_type', 'other'),
                author=source_data.get('author', ''),
                year=source_data.get('year'),
                url=source_data.get('url', ''),
                isbn=source_data.get('isbn', ''),
                notes=source_data.get('notes', ''),
            )
            create_values['id'] = source_id
            source = Source.objects.create(**create_values)
            self.runtime.log_success(f'Создан источник: {source}')
            return source
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка создания источника: {error}',
                error,
            )
            return None

    def _find_existing(self, source_data):
        source_id = source_data.get('id') or source_data.get('uuid')
        if not source_id:
            return None
        return self.runtime.get_by_uuid(Source, str(source_id))

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
