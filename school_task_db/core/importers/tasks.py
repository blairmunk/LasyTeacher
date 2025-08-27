"""
Импортер заданий с поддержкой UUID и зависимостей
"""
import uuid
from typing import Dict, List, Any, Optional
from django.db import transaction

from .base import BaseImporter, ImportContext
from tasks.models import Task, TaskImage
from task_groups.models import AnalogGroup, TaskGroup
from curriculum.models import Topic, SubTopic

class TaskImporter(BaseImporter):
    """Импортер заданий с полной поддержкой зависимостей"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = ImportContext()
    
    def import_tasks_from_json(self, json_data: Dict[str, Any]) -> ImportContext:
        """Основной метод импорта заданий из JSON"""
        
        if self.dry_run:
            print("🔍 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР (--dry-run)")
            return self._preview_import(json_data)
        
        with transaction.atomic():
            print("🚀 ИМПОРТ ЗАДАНИЙ:")
            
            # ЭТАП 1: Импорт групп аналогов
            if 'analog_groups' in json_data:
                self._import_analog_groups(json_data['analog_groups'])
            
            # ЭТАП 2: Импорт тем (если есть и разрешено создавать)
            if 'topics' in json_data and self.create_missing:
                self._import_topics(json_data['topics'])
            
            # ЭТАП 3: Импорт заданий
            if 'tasks' in json_data:
                self._import_tasks(json_data['tasks'])
            
            # ЭТАП 4: Создание связей задание-группа
            self._create_task_group_relations(json_data)
            
            # ЭТАП 5: Импорт изображений (если есть)
            if 'task_images' in json_data:
                self._import_task_images(json_data['task_images'])
        
        return self.context
    
    def _preview_import(self, json_data: Dict[str, Any]) -> ImportContext:
        """Предварительный просмотр импорта"""
        tasks_data = json_data.get('tasks', [])
        groups_data = json_data.get('analog_groups', [])
        topics_data = json_data.get('topics', [])
        
        print(f"  📝 Заданий в файле: {len(tasks_data)}")
        print(f"  📋 Групп аналогов: {len(groups_data)}")
        print(f"  📚 Тем: {len(topics_data)}")
        
        # Анализ UUID конфликтов
        self._analyze_uuid_conflicts(json_data)
        
        # Анализ зависимостей
        self._analyze_dependencies(json_data)
        
        return self.context
    
    def _import_analog_groups(self, groups_data: List[Dict[str, Any]]):
        """Импорт групп аналогов"""
        print("📋 Импорт групп аналогов...")
        
        for group_data in groups_data:
            try:
                group_uuid = self.generate_uuid_if_missing(group_data, 'id')
                
                # Поиск существующей группы
                existing_group = self.safe_get_by_uuid(AnalogGroup, group_uuid)
                
                if existing_group and not self.should_create_object(existing_group, group_data):
                    if self.mode == 'update':
                        self._update_analog_group(existing_group, group_data)
                        self.context.add_group(group_uuid, existing_group)
                        self.stats.updated += 1
                    else:  # skip
                        self.context.add_group(group_uuid, existing_group)
                    continue
                
                # Создание новой группы
                if not existing_group:
                    group = AnalogGroup.objects.create(
                        id=group_uuid,
                        name=group_data['name'],
                        description=group_data.get('description', '')
                    )
                    
                    self.context.add_group(group_uuid, group)
                    self.stats.created += 1
                    self.log_success(f"Создана группа: {group.name} [{group.get_short_uuid()}]")
                
            except Exception as e:
                self.log_error(f"Ошибка импорта группы {group_data.get('name', 'Unknown')}: {e}", e)
    
    def _import_topics(self, topics_data: List[Dict[str, Any]]):
        """Импорт тем (если создание зависимостей разрешено)"""
        print("📚 Импорт тем...")
        
        for topic_data in topics_data:
            try:
                topic = self._find_or_create_topic(topic_data)
                if topic:
                    # UUID может не быть в данных темы, генерируем на основе содержимого
                    topic_key = f"{topic.subject}_{topic.grade_level}_{topic.name}"
                    self.context.add_topic(topic_key, topic)
                    
            except Exception as e:
                self.log_error(f"Ошибка импорта темы {topic_data.get('name', 'Unknown')}: {e}", e)
    
    def _import_tasks(self, tasks_data: List[Dict[str, Any]]):
        """Импорт заданий"""
        print("📝 Импорт заданий...")
        
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
        topic = self._find_or_create_topic(task_data.get('topic'))
        if not topic:
            self.log_error(f"Не удалось найти/создать тему для задания {task_uuid[-8:]}")
            return None
        
        # Поиск подтемы (опционально)
        subtopic = None
        if 'subtopic' in task_data:
            subtopic = self._find_or_create_subtopic(task_data['subtopic'], topic)
        
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
            estimated_time=task_data.get('estimated_time')
        )
        
        return task
    
    def _find_or_create_topic(self, topic_data: Any) -> Optional[Topic]:
        """Поиск или создание темы"""
        if not topic_data:
            return None
        
        # Поиск существующей темы
        topic = self._find_topic(topic_data)
        if topic:
            return topic
        
        # Создание новой темы если разрешено
        if self.create_missing and isinstance(topic_data, dict):
            try:
                topic = Topic.objects.create(
                    name=topic_data['name'],
                    subject=topic_data.get('subject', 'Не указан'),
                    grade_level=topic_data.get('grade_level'),
                    section=topic_data.get('section', ''),
                    description=topic_data.get('description', ''),
                    order=topic_data.get('order', 1)
                )
                self.log_success(f"Создана тема: {topic.name}")
                return topic
            except Exception as e:
                self.log_error(f"Ошибка создания темы: {e}", e)
        
        return None
    
    def _find_topic(self, topic_data: Any) -> Optional[Topic]:
        """Поиск темы по данным"""
        if not topic_data:
            return None
        
        if isinstance(topic_data, str):
            return Topic.objects.filter(name=topic_data).first()
        
        elif isinstance(topic_data, dict):
            filters = {}
            if 'name' in topic_data:
                filters['name'] = topic_data['name']
            if 'subject' in topic_data:
                filters['subject'] = topic_data['subject']
            if 'grade_level' in topic_data:
                filters['grade_level'] = topic_data['grade_level']
            
            if filters:
                return Topic.objects.filter(**filters).first()
        
        return None
    
    def _create_task_group_relations(self, json_data: Dict[str, Any]):
        """Создание связей задание-группа"""
        print("🔗 Создание связей заданий с группами...")
        
        relations_created = 0
        
        for task_data in json_data.get('tasks', []):
            task_uuid = task_data.get('id')
            
            if task_uuid not in self.context.imported_tasks:
                continue
            
            task = self.context.imported_tasks[task_uuid]
            
            # Связи через UUID групп
            for group_uuid in task_data.get('groups', []):
                if group_uuid in self.context.imported_groups:
                    group = self.context.imported_groups[group_uuid]
                    if self._create_task_group_relation(task, group):
                        relations_created += 1
                else:
                    # Поиск группы в базе
                    existing_group = self.safe_get_by_uuid(AnalogGroup, group_uuid)
                    if existing_group and self._create_task_group_relation(task, existing_group):
                        relations_created += 1
            
            # Связи через имя группы (fallback)
            group_name = task_data.get('group_name')
            if group_name and not task_data.get('groups'):
                group = self._get_or_create_group_by_name(group_name)
                if group and self._create_task_group_relation(task, group):
                    relations_created += 1
        
        print(f"  ✅ Создано связей: {relations_created}")
    
    def _create_task_group_relation(self, task, group) -> bool:
        """Создание связи задание-группа"""
        try:
            relation, created = TaskGroup.objects.get_or_create(
                task=task,
                group=group
            )
            
            if created:
                self.log_info(f"Связь: {task.get_short_uuid()} ↔ {group.get_short_uuid()}")
            
            return created
            
        except Exception as e:
            self.log_error(f"Ошибка создания связи: {e}", e)
            return False
    
    def _get_or_create_group_by_name(self, group_name: str):
        """Получение или создание группы по имени"""
        existing_group = AnalogGroup.objects.filter(name=group_name).first()
        if existing_group:
            return existing_group
        
        if self.create_missing:
            try:
                group = AnalogGroup.objects.create(
                    name=group_name,
                    description="Автоматически создана при импорте заданий"
                )
                self.log_success(f"Создана группа: {group_name}")
                return group
            except Exception as e:
                self.log_error(f"Ошибка создания группы {group_name}: {e}", e)
        
        return None

    def _import_task_images(self, images_data: List[Dict[str, Any]]):
        """Импорт изображений заданий"""
        print("🖼️ Импорт изображений заданий...")
        
        for image_data in images_data:
            try:
                task_uuid = image_data.get('task_id')
                if task_uuid not in self.context.imported_tasks:
                    self.log_warning(f"Задание не найдено для изображения: {task_uuid[-8:]}")
                    continue
                
                task = self.context.imported_tasks[task_uuid]
                
                # Создание изображения из base64 или файла
                # ... логика импорта изображений
                
            except Exception as e:
                self.log_error(f"Ошибка импорта изображения: {e}", e)
    
    def _analyze_uuid_conflicts(self, json_data: Dict[str, Any]):
        """Анализ конфликтов UUID"""
        print("\n📊 UUID АНАЛИЗ:")
        
        # ... код анализа UUID как в предыдущей версии ...
    
    def _analyze_dependencies(self, json_data: Dict[str, Any]):
        """Анализ зависимостей"""
        print("\n🔍 АНАЛИЗ ЗАВИСИМОСТЕЙ:")
        
        # ... код анализа зависимостей как в предыдущей версии ...
    
    # Остальные вспомогательные методы...
