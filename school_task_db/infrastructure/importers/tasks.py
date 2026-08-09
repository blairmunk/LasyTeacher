"""
Импортер заданий с поддержкой UUID и зависимостей
"""
from typing import Dict, List, Any, Optional

from django.db import transaction

from .base import BaseImporter, ImportContext
from tasks.models import Task
from .task_groups import TaskGroupImporter
from .task_images import TaskImageImporter
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
        tasks_data = json_data.get('tasks', [])
        groups_data = json_data.get('analog_groups', [])
        topics_data = json_data.get('topics', [])
        
        self._write(f"  📝 Заданий в файле: {len(tasks_data)}")
        self._write(f"  📋 Групп аналогов: {len(groups_data)}")
        self._write(f"  📚 Тем: {len(topics_data)}")
        
        # Анализ UUID конфликтов
        uuid_counts = self._analyze_uuid_conflicts(json_data)
        
        # Анализ зависимостей
        self._analyze_dependencies(json_data)

        self.context.preview_summary = {
            'file_counts': {
                'tasks': len(tasks_data),
                'groups': len(groups_data),
                'topics': len(topics_data),
                'sources': len(json_data.get('sources', [])),
                'images': len(json_data.get('task_images', [])),
            },
            'task_uuid_counts': uuid_counts['tasks'],
            'group_uuid_counts': uuid_counts['groups'],
        }
        
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
    
    def _analyze_uuid_conflicts(self, json_data: Dict[str, Any]):
        """Анализ конфликтов UUID"""
        self._write("\n📊 UUID АНАЛИЗ:")
        
        tasks_data = json_data.get('tasks', [])
        groups_data = json_data.get('analog_groups', [])
        images_data = json_data.get('task_images', [])
        
        # Анализ заданий
        task_conflicts = {'existing': [], 'new': [], 'invalid': []}
        for i, task_data in enumerate(tasks_data):
            task_uuid = task_data.get('id')
            
            if not task_uuid:
                task_conflicts['invalid'].append(f"Задание {i}: UUID отсутствует")
                continue
            
            try:
                import uuid
                uuid.UUID(task_uuid)  # Валидация формата
                
                existing_task = self.safe_get_by_uuid(Task, task_uuid)
                if existing_task:
                    task_conflicts['existing'].append(task_uuid)
                else:
                    task_conflicts['new'].append(task_uuid)
                    
            except ValueError:
                task_conflicts['invalid'].append(f"Задание {i}: некорректный UUID '{task_uuid}'")
        
        # Анализ групп
        group_conflicts = {'existing': [], 'new': [], 'invalid': []}
        for i, group_data in enumerate(groups_data):
            group_uuid = group_data.get('id')
            
            if not group_uuid:
                group_conflicts['invalid'].append(f"Группа {i}: UUID отсутствует")
                continue
                
            try:
                import uuid
                uuid.UUID(group_uuid)
                
                existing_group = self.group_importer.find_by_uuid(group_uuid)
                if existing_group:
                    group_conflicts['existing'].append(group_uuid)
                else:
                    group_conflicts['new'].append(group_uuid)
                    
            except ValueError:
                group_conflicts['invalid'].append(f"Группа {i}: некорректный UUID '{group_uuid}'")
        
        # Вывод анализа
        self._write(f"  📝 ЗАДАНИЯ:")
        self._write(f"    🆕 Новых: {len(task_conflicts['new'])}")
        self._write(f"    🔄 Существующих: {len(task_conflicts['existing'])}")
        self._write(f"    ❌ Некорректных UUID: {len(task_conflicts['invalid'])}")
        
        self._write(f"  📋 ГРУППЫ:")
        self._write(f"    🆕 Новых: {len(group_conflicts['new'])}")
        self._write(f"    🔄 Существующих: {len(group_conflicts['existing'])}")
        self._write(f"    ❌ Некорректных UUID: {len(group_conflicts['invalid'])}")
        
        if images_data:
            self._write(f"  🖼️ ИЗОБРАЖЕНИЯ: {len(images_data)}")
        
        # Предупреждения
        if task_conflicts['existing'] and self.mode == 'strict':
            self._write(f"  ⚠️ В режиме strict будут ошибки для {len(task_conflicts['existing'])} существующих заданий")
        
        if task_conflicts['invalid'] or group_conflicts['invalid']:
            self._write(f"  🚨 Некорректные UUID будут пропущены")

        return {
            'tasks': {
                key: len(values)
                for key, values in task_conflicts.items()
            },
            'groups': {
                key: len(values)
                for key, values in group_conflicts.items()
            },
        }

    def _analyze_dependencies(self, json_data: Dict[str, Any]):
        """Анализ зависимостей"""
        self._write("\n🔍 АНАЛИЗ ЗАВИСИМОСТЕЙ:")
        
        tasks_data = json_data.get('tasks', [])
        missing_topics = set()
        missing_groups = set()
        broken_references = []
        
        # Анализ тем
        for i, task_data in enumerate(tasks_data):
            topic_data = task_data.get('topic')
            if topic_data:
                topic = self.topic_importer.find(topic_data)
                if not topic:
                    if isinstance(topic_data, dict):
                        topic_key = f"{topic_data.get('subject', 'Unknown')} - {topic_data.get('name', 'Unknown')}"
                        if topic_data.get('grade_level'):
                            topic_key += f" ({topic_data['grade_level']} класс)"
                    else:
                        topic_key = str(topic_data)
                    missing_topics.add(topic_key)
        
        # Анализ связей с группами
        declared_group_uuids = {g.get('id') for g in json_data.get('analog_groups', []) if g.get('id')}
        
        for i, task_data in enumerate(tasks_data):
            task_text = task_data.get('text', 'Unknown')[:30]
            
            # Проверяем UUID группы
            for group_ref in task_data.get('groups', []):
                try:
                    group_uuid, _bank_role = self.group_importer.parse_reference(
                        group_ref,
                    )
                except ValueError as error:
                    broken_references.append(
                        f"Задание '{task_text}' → {error}"
                    )
                    continue
                if not group_uuid:
                    broken_references.append(
                        f"Задание '{task_text}' → группа без id"
                    )
                    continue
                if group_uuid not in declared_group_uuids:
                    # Проверяем в базе данных
                    existing_group = self.group_importer.find_by_uuid(group_uuid)
                    if not existing_group:
                        missing_groups.add(group_uuid)
                        broken_references.append(f"Задание '{task_text}' → группа {group_uuid[-8:]}")
            
            # Проверяем имя группы (fallback)
            group_name = task_data.get('group_name')
            if group_name and not task_data.get('groups'):
                if not self.group_importer.exists_by_name(group_name):
                    missing_groups.add(f"По имени: {group_name}")
        
        # Вывод анализа зависимостей
        if missing_topics:
            self._write(f"  📚 ОТСУТСТВУЮЩИЕ ТЕМЫ: {len(missing_topics)}")
            for topic in sorted(list(missing_topics))[:3]:
                self._write(f"    - {topic}")
            if len(missing_topics) > 3:
                self._write(f"    ... и еще {len(missing_topics) - 3}")
            
            if self.create_missing:
                self._write(f"    ✅ Будут созданы автоматически (--create-topics)")
            else:
                self._write(f"    ⚠️ Задания без тем будут пропущены (используйте --create-topics)")
        
        if missing_groups:
            self._write(f"  📋 ОТСУТСТВУЮЩИЕ ГРУППЫ: {len(missing_groups)}")
            for group in sorted(list(missing_groups))[:3]:
                self._write(f"    - {group}")
            if len(missing_groups) > 3:
                self._write(f"    ... и еще {len(missing_groups) - 3}")
                
            if self.create_missing:
                self._write(f"    ✅ Будут созданы автоматически (--create-groups)")
            else:
                self._write(f"    ⚠️ Связи будут пропущены (используйте --create-groups)")
        
        if broken_references:
            self._write(f"  🔗 ПРОБЛЕМНЫЕ СВЯЗИ: {len(broken_references)}")
            for ref in broken_references[:3]:
                self._write(f"    - {ref}")
            if len(broken_references) > 3:
                self._write(f"    ... и еще {len(broken_references) - 3}")
        
        # Рекомендации
        recommendations = []
        if missing_topics and not self.create_missing:
            recommendations.append("Добавьте --create-topics для автоматического создания тем")
        if missing_groups and not self.create_missing:
            recommendations.append("Добавьте --create-groups для автоматического создания групп")
        if broken_references:
            recommendations.append("Проверьте UUID групп в JSON файле")
        
        if recommendations:
            self._write(f"  💡 РЕКОМЕНДАЦИИ:")
            for rec in recommendations:
                self._write(f"    • {rec}")

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
