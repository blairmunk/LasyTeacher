"""
Импортер заданий с поддержкой UUID и зависимостей
"""
from typing import Dict, List, Any, Optional

from django.db import transaction

from .base import BaseImporter, ImportContext
from tasks.models import Task
from .task_groups import TaskGroupImporter
from .task_images import TaskImageImporter
from .task_preview import TaskImportPreviewAnalyzer
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
                self._import_tasks(json_data['tasks'])
            
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
    
    def _import_tasks(self, tasks_data: List[Dict[str, Any]]):
        """Импорт заданий"""
        self._write("📝 Импорт заданий...")
        
        for task_data in tasks_data:
            try:
                task_uuid = self.generate_uuid_if_missing(task_data, 'id')
                
                # Поиск существующего задания
                existing_task = self.safe_get_by_uuid(Task, task_uuid)
                
                if existing_task and not self.should_create_object(existing_task, task_data):
                    if self.mode == 'update':
                        self._update_task(existing_task, task_data)
                        self.context.add_task(task_uuid, existing_task)
                        self.stats.updated += 1
                    else:  # skip
                        self.context.add_task(task_uuid, existing_task)
                    continue
                
                # Создание нового задания
                if not existing_task:
                    task = self._create_task(task_uuid, task_data)
                    if task:
                        self.context.add_task(task_uuid, task)
                        self.stats.created += 1
                        self.log_success(f"Создано задание: {task.get_short_uuid()}")
                
            except Exception as e:
                task_preview = task_data.get('text', 'Unknown')[:30]
                self.log_error(f"Ошибка импорта задания '{task_preview}': {e}", e)
    
    def _create_task(self, task_uuid: str, task_data: Dict[str, Any]) -> Optional[Task]:
        """Создание нового задания"""
        
        # Поиск темы
        topic = self.topic_importer.resolve(task_data.get('topic'))
        if not topic:
            self.log_error(f"Не удалось найти/создать тему для задания {task_uuid[-8:]}")
            return None
        
        # Поиск подтемы (опционально)
        subtopic = None
        if 'subtopic' in task_data:
            subtopic = self.topic_importer.resolve_subtopic(
                task_data['subtopic'],
                topic,
            )
        
        # Поиск источника
        source = self.source_importer.resolve(task_data.get('source'))

        # Создание задания
        task = Task.objects.create(
            id=task_uuid,
            text=task_data['text'],
            answer=task_data.get('answer', ''),
            short_solution=task_data.get('short_solution', ''),
            full_solution=task_data.get('full_solution', ''),
            hint=task_data.get('hint', ''),
            instruction=task_data.get('instruction', ''),
            topic=topic,
            subtopic=subtopic,
            content_element=task_data.get('content_element', ''),
            requirement_element=task_data.get('requirement_element', ''),
            task_type=task_data.get('task_type', 'theoretical'),
            difficulty=task_data.get('difficulty', 3),
            cognitive_level=task_data.get('cognitive_level', 'understand'),
            estimated_time=task_data.get('estimated_time'),
            # Новые поля
            source=source,
            source_detail=task_data.get('source_detail', ''),
            grade=task_data.get('grade'),
            year=task_data.get('year'),
            is_verified=task_data.get('is_verified', False),
            teacher_notes=task_data.get('teacher_notes', ''),
        )
        
        return task
    
    def _update_task(self, task: Task, task_data: Dict[str, Any]):
        """Обновление существующего задания"""
        try:
            # Обновляем основные поля
            task.text = task_data.get('text', task.text)
            task.answer = task_data.get('answer', task.answer)
            task.short_solution = task_data.get('short_solution', task.short_solution)
            task.full_solution = task_data.get('full_solution', task.full_solution)
            task.hint = task_data.get('hint', task.hint)
            task.instruction = task_data.get('instruction', task.instruction)
            
            # Обновляем метаданные
            task.content_element = task_data.get('content_element', task.content_element)
            task.requirement_element = task_data.get('requirement_element', task.requirement_element)
            task.task_type = task_data.get('task_type', task.task_type)
            task.difficulty = task_data.get('difficulty', task.difficulty)
            task.cognitive_level = task_data.get('cognitive_level', task.cognitive_level)
            task.estimated_time = task_data.get('estimated_time', task.estimated_time)
            
            # Обновляем тему если указана
            topic_data = task_data.get('topic')
            if topic_data:
                topic = self.topic_importer.resolve(topic_data)
                if topic:
                    task.topic = topic
                    if 'subtopic' in task_data:
                        task.subtopic = self.topic_importer.resolve_subtopic(
                            task_data['subtopic'],
                            topic,
                        )

            # Обновляем новые поля
            if 'source' in task_data:
                source = self.source_importer.resolve(task_data['source'])
                if source:
                    task.source = source
            if 'source_detail' in task_data:
                task.source_detail = task_data['source_detail']
            if 'grade' in task_data:
                task.grade = task_data['grade']
            if 'year' in task_data:
                task.year = task_data['year']
            if 'is_verified' in task_data:
                task.is_verified = task_data['is_verified']
            if 'teacher_notes' in task_data:
                task.teacher_notes = task_data['teacher_notes']
            
            task.save()
            self.log_success(f"Обновлено задание: {task.get_short_uuid()}")
            
        except Exception as e:
            self.log_error(f"Ошибка обновления задания: {e}", e)
