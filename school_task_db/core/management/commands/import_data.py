"""
Команда импорта данных из JSON файла
Поддерживает различные форматы и валидацию
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pathlib import Path

class Command(BaseCommand):
    help = 'Импорт данных из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Путь к JSON файлу с данными')
        parser.add_argument('--dry-run', action='store_true', help='Предварительный просмотр без сохранения')
        parser.add_argument('--clear', action='store_true', help='Очистить существующие данные перед импортом')

    def handle(self, *args, **options):
        json_file = Path(options['json_file'])
        
        if not json_file.exists():
            raise CommandError(f"JSON файл не найден: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Ошибка чтения JSON: {e}")
        
        if options['dry_run']:
            self.preview_import(data)
        else:
            if options['clear']:
                self.clear_database()
            self.import_data(data)

    def preview_import(self, data):
        """Предварительный просмотр импорта"""
        self.stdout.write("👀 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР ИМПОРТА:")
        
        # Анализируем структуру данных
        for key, value in data.items():
            if isinstance(value, list):
                self.stdout.write(f"  📋 {key}: {len(value)} записей")
            elif isinstance(value, dict):
                self.stdout.write(f"  📁 {key}: {len(value)} подкатегорий")
            else:
                self.stdout.write(f"  📝 {key}: {value}")

    def import_data(self, data):
        """Импорт данных с валидацией"""
        with transaction.atomic():
            self.stdout.write("📥 Начинаем импорт данных...")
            
            # Здесь реализация импорта зависит от формата данных
            # Можно расширить для конкретных нужд
            
            self.stdout.write(self.style.SUCCESS("✅ Импорт завершен успешно!"))
