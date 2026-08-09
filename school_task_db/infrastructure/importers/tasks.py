"""
Импортер заданий с поддержкой UUID и зависимостей
"""
from typing import Any, Dict

from django.db import transaction

from .base import BaseImporter, ImportContext
from .task_groups import TaskGroupImporter
from .task_images import TaskImageImporter
from .task_preview import TaskImportPreviewAnalyzer
from .task_records import TaskRecordImporter
from .task_sources import TaskSourceImporter
from .task_topics import TaskTopicImporter


class TaskImporter(BaseImporter):
    """Импортер заданий с полной поддержкой зависимостей"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = ImportContext()
        self.image_importer = TaskImageImporter(self, self.context)
        self.group_importer = TaskGroupImporter(self, self.context)
        self.source_importer = TaskSourceImporter(self)
        self.topic_importer = TaskTopicImporter(self, self.context)
        self.record_importer = TaskRecordImporter(
            self,
            self.context,
            self.topic_importer,
            self.source_importer,
        )
        self.preview_analyzer = TaskImportPreviewAnalyzer(
            self,
            self.group_importer,
            self.topic_importer,
        )
    
    def import_tasks_from_json(self, json_data: Dict[str, Any]) -> ImportContext:
        """Основной метод импорта заданий из JSON"""
        
        if self.dry_run:
            self._write("🔍 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР (--dry-run)")
            return self._preview_import(json_data)
        
        with transaction.atomic():
            self._write("🚀 ИМПОРТ ЗАДАНИЙ:")

            # ЭТАП 0: Импорт источников
            if 'sources' in json_data:
                self.source_importer.import_sources(json_data['sources'])
            
            # ЭТАП 1: Импорт групп аналогов
            if 'analog_groups' in json_data:
                self.group_importer.import_groups(json_data['analog_groups'])
            
            # ЭТАП 2: Импорт тем (если есть и разрешено создавать)
            if 'topics' in json_data and self.create_missing:
                self.topic_importer.import_topics(json_data['topics'])
            
            # ЭТАП 3: Импорт заданий
            if 'tasks' in json_data:
                self.record_importer.import_tasks(json_data['tasks'])
            
            # ЭТАП 4: Создание связей задание-группа
            self.group_importer.create_task_relations(
                json_data.get('tasks', []),
            )
            
            # ЭТАП 5: Импорт изображений (если есть)
            if 'task_images' in json_data:
                self.image_importer.import_images(json_data['task_images'])
        
        return self.context
    
    def _preview_import(self, json_data: Dict[str, Any]) -> ImportContext:
        """Предварительный просмотр импорта"""
        self.context.preview_summary = self.preview_analyzer.analyze(json_data)
        return self.context
