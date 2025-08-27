"""
UUID-ориентированная команда импорта заданий
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

from core.importers.tasks import TaskImporter

class Command(BaseCommand):
    help = 'Импорт заданий из JSON с полной поддержкой UUID'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='JSON файл с заданиями')
        parser.add_argument('--mode', choices=['strict', 'update', 'skip'], default='update',
                           help='Режим обработки существующих UUID')
        parser.add_argument('--create-groups', action='store_true', 
                           help='Создавать отсутствующие группы автоматически')
        parser.add_argument('--create-topics', action='store_true',
                           help='Создавать отсутствующие темы автоматически')
        parser.add_argument('--dry-run', action='store_true', help='Предварительный просмотр')
        parser.add_argument('--verbose', action='store_true', help='Подробный вывод')

    def handle(self, *args, **options):
        # Чтение JSON файла
        json_file = Path(options['json_file'])
        if not json_file.exists():
            raise CommandError(f"JSON файл не найден: {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Ошибка чтения JSON: {e}")

        # Создание и настройка импортера
        importer = TaskImporter(
            mode=options['mode'],
            dry_run=options['dry_run'],
            verbose=options['verbose'],
            create_missing=options['create_groups'] or options['create_topics']
        )

        # Валидация режима
        importer.validate_mode()

        # Выполнение импорта
        try:
            context = importer.import_tasks_from_json(data)
            importer.print_import_summary()
            
            # Вывод статистики контекста
            context_stats = context.get_stats_summary()
            if any(context_stats.values()):
                self.stdout.write("\n🎯 ИМПОРТИРОВАНО В КОНТЕКСТ:")
                for obj_type, count in context_stats.items():
                    if count > 0:
                        self.stdout.write(f"  {obj_type}: {count}")
            
        except Exception as e:
            raise CommandError(f"Ошибка импорта: {e}")
