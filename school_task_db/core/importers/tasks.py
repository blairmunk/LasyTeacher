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
        """Импорт изображений заданий из base64 или файлов"""
        print("🖼️ Импорт изображений заданий...")
        
        for image_data in images_data:
            try:
                task_uuid = image_data.get('task_uuid') or image_data.get('task_id')
                
                if task_uuid not in self.context.imported_tasks:
                    self.log_warning(f"Задание не найдено для изображения: {task_uuid[-8:] if task_uuid else 'Unknown'}")
                    continue
                
                task = self.context.imported_tasks[task_uuid]
                
                # Генерируем UUID для изображения
                image_uuid = self.generate_uuid_if_missing(image_data, 'id')
                
                # Проверяем существующее изображение
                existing_image = self.safe_get_by_uuid(TaskImage, image_uuid)
                if existing_image and not self.should_create_object(existing_image, image_data):
                    if self.mode == 'update':
                        self._update_task_image(existing_image, image_data)
                        self.stats.updated += 1
                    else:  # skip
                        pass
                    continue
                
                # Создание нового изображения
                if not existing_image:
                    image = self._create_task_image(task, image_uuid, image_data)
                    if image:
                        self.stats.created += 1
                        self.log_success(f"Создано изображение для задания {task.get_short_uuid()}")
                
            except Exception as e:
                self.log_error(f"Ошибка импорта изображения: {e}", e)

    def _create_task_image(self, task: Task, image_uuid: str, image_data: Dict[str, Any]) -> Optional[TaskImage]:
        """Создание изображения задания"""
        try:
            # ИСПРАВЛЕНО: Валидация UUID формата
            import uuid as uuid_module
            
            try:
                # Проверяем что UUID валидный
                uuid_obj = uuid_module.UUID(image_uuid)
                self.log_info(f"UUID валиден: {str(uuid_obj)[-8:]}")
            except ValueError as e:
                self.log_error(f"Некорректный UUID изображения: {image_uuid} - {e}")
                return None
            
            # Обработка содержимого изображения
            image_content = None
            filename = image_data.get('filename', 'imported_image.jpg')
            
            if 'base64_data' in image_data:
                # Импорт из base64
                import base64
                from django.core.files.base import ContentFile
                
                try:
                    # Убираем префикс data:image/...;base64, если есть
                    base64_string = image_data['base64_data']
                    if ',' in base64_string:
                        base64_string = base64_string.split(',')[1]
                    
                    image_content = ContentFile(
                        base64.b64decode(base64_string),
                        name=filename
                    )
                    self.log_info(f"Base64 декодирован: {len(base64_string)} символов")
                except Exception as e:
                    self.log_error(f"Ошибка декодирования base64: {e}", e)
                    return None
                    
            elif hasattr(self, 'images_dir') and self.images_dir and 'filename' in image_data:
                # Импорт из файла
                from pathlib import Path
                from django.core.files.base import ContentFile
                
                image_path = Path(self.images_dir) / image_data['filename']
                if image_path.exists():
                    with open(image_path, 'rb') as f:
                        image_content = ContentFile(f.read(), name=filename)
                else:
                    self.log_warning(f"Файл изображения не найден: {image_path}")
                    return None
            else:
                self.log_warning(f"Нет данных изображения (base64_data или filename)")
                return None
            
            if image_content:
                # ИЗМЕНЕНО: НЕ устанавливаем position по умолчанию
                position = image_data.get('position', '')  # Пустая строка вместо 'bottom_70'
                
                task_image = TaskImage.objects.create(
                    id=image_uuid,
                    task=task,
                    image=image_content,
                    position=position,  # Может быть пустой строкой
                    caption=image_data.get('caption', ''),
                    order=image_data.get('order', 1)
                )
                
                # ДОБАВЛЕНО: Логирование статуса позиции
                if position:
                    self.log_info(f"Изображение создано с позицией: {position}")
                else:
                    self.log_info(f"Изображение создано БЕЗ позиции (для настройки позже)")
                    self.stats.add_warning(f"Изображение {image_uuid[-8:]} создано без позиции")
                
                return task_image
            
        except Exception as e:
            self.log_error(f"Ошибка создания изображения: {e}", e)
            self.log_error(f"UUID: {image_uuid}")
            self.log_error(f"Task: {task}")
            self.log_error(f"Image data keys: {list(image_data.keys())}")
        
        return None

    def _update_task_image(self, image: TaskImage, image_data: Dict[str, Any]):
        """Обновление существующего изображения"""
        try:
            # Обновляем метаданные
            image.position = image_data.get('position', image.position)
            image.caption = image_data.get('caption', image.caption)
            image.order = image_data.get('order', image.order)
            
            # Обновляем файл изображения если есть новые данные
            if 'base64_data' in image_data:
                import base64
                from django.core.files.base import ContentFile
                
                base64_string = image_data['base64_data']
                if ',' in base64_string:
                    base64_string = base64_string.split(',')[1]
                
                filename = image_data.get('filename', f'updated_{image.image.name}')
                new_content = ContentFile(
                    base64.b64decode(base64_string),
                    name=filename
                )
                image.image = new_content
            
            image.save()
            self.log_success(f"Обновлено изображение {image.get_short_uuid()}")
            
        except Exception as e:
            self.log_error(f"Ошибка обновления изображения: {e}", e)

    def _analyze_uuid_conflicts(self, json_data: Dict[str, Any]):
        """Анализ конфликтов UUID"""
        print("\n📊 UUID АНАЛИЗ:")
        
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
                
                existing_group = self.safe_get_by_uuid(AnalogGroup, group_uuid)
                if existing_group:
                    group_conflicts['existing'].append(group_uuid)
                else:
                    group_conflicts['new'].append(group_uuid)
                    
            except ValueError:
                group_conflicts['invalid'].append(f"Группа {i}: некорректный UUID '{group_uuid}'")
        
        # Вывод анализа
        print(f"  📝 ЗАДАНИЯ:")
        print(f"    🆕 Новых: {len(task_conflicts['new'])}")
        print(f"    🔄 Существующих: {len(task_conflicts['existing'])}")
        print(f"    ❌ Некорректных UUID: {len(task_conflicts['invalid'])}")
        
        print(f"  📋 ГРУППЫ:")
        print(f"    🆕 Новых: {len(group_conflicts['new'])}")
        print(f"    🔄 Существующих: {len(group_conflicts['existing'])}")
        print(f"    ❌ Некорректных UUID: {len(group_conflicts['invalid'])}")
        
        if images_data:
            print(f"  🖼️ ИЗОБРАЖЕНИЯ: {len(images_data)}")
        
        # Предупреждения
        if task_conflicts['existing'] and self.mode == 'strict':
            print(f"  ⚠️ В режиме strict будут ошибки для {len(task_conflicts['existing'])} существующих заданий")
        
        if task_conflicts['invalid'] or group_conflicts['invalid']:
            print(f"  🚨 Некорректные UUID будут пропущены")

    def _analyze_dependencies(self, json_data: Dict[str, Any]):
        """Анализ зависимостей"""
        print("\n🔍 АНАЛИЗ ЗАВИСИМОСТЕЙ:")
        
        tasks_data = json_data.get('tasks', [])
        missing_topics = set()
        missing_groups = set()
        broken_references = []
        
        # Анализ тем
        for i, task_data in enumerate(tasks_data):
            topic_data = task_data.get('topic')
            if topic_data:
                topic = self._find_topic(topic_data)
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
            for group_uuid in task_data.get('groups', []):
                if group_uuid not in declared_group_uuids:
                    # Проверяем в базе данных
                    existing_group = self.safe_get_by_uuid(AnalogGroup, group_uuid)
                    if not existing_group:
                        missing_groups.add(group_uuid)
                        broken_references.append(f"Задание '{task_text}' → группа {group_uuid[-8:]}")
            
            # Проверяем имя группы (fallback)
            group_name = task_data.get('group_name')
            if group_name and not task_data.get('groups'):
                if not AnalogGroup.objects.filter(name=group_name).exists():
                    missing_groups.add(f"По имени: {group_name}")
        
        # Вывод анализа зависимостей
        if missing_topics:
            print(f"  📚 ОТСУТСТВУЮЩИЕ ТЕМЫ: {len(missing_topics)}")
            for topic in sorted(list(missing_topics))[:3]:
                print(f"    - {topic}")
            if len(missing_topics) > 3:
                print(f"    ... и еще {len(missing_topics) - 3}")
            
            if self.create_missing:
                print(f"    ✅ Будут созданы автоматически (--create-topics)")
            else:
                print(f"    ⚠️ Задания без тем будут пропущены (используйте --create-topics)")
        
        if missing_groups:
            print(f"  📋 ОТСУТСТВУЮЩИЕ ГРУППЫ: {len(missing_groups)}")
            for group in sorted(list(missing_groups))[:3]:
                print(f"    - {group}")
            if len(missing_groups) > 3:
                print(f"    ... и еще {len(missing_groups) - 3}")
                
            if self.create_missing:
                print(f"    ✅ Будут созданы автоматически (--create-groups)")
            else:
                print(f"    ⚠️ Связи будут пропущены (используйте --create-groups)")
        
        if broken_references:
            print(f"  🔗 ПРОБЛЕМНЫЕ СВЯЗИ: {len(broken_references)}")
            for ref in broken_references[:3]:
                print(f"    - {ref}")
            if len(broken_references) > 3:
                print(f"    ... и еще {len(broken_references) - 3}")
        
        # Рекомендации
        recommendations = []
        if missing_topics and not self.create_missing:
            recommendations.append("Добавьте --create-topics для автоматического создания тем")
        if missing_groups and not self.create_missing:
            recommendations.append("Добавьте --create-groups для автоматического создания групп")
        if broken_references:
            recommendations.append("Проверьте UUID групп в JSON файле")
        
        if recommendations:
            print(f"  💡 РЕКОМЕНДАЦИИ:")
            for rec in recommendations:
                print(f"    • {rec}")

    def _update_analog_group(self, group: AnalogGroup, group_data: Dict[str, Any]):
        """Обновление существующей группы аналогов"""
        try:
            group.name = group_data.get('name', group.name)
            group.description = group_data.get('description', group.description)
            group.save()
            
            self.log_success(f"Обновлена группа: {group.name} [{group.get_short_uuid()}]")
            
        except Exception as e:
            self.log_error(f"Ошибка обновления группы: {e}", e)

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
                topic = self._find_or_create_topic(topic_data)
                if topic:
                    task.topic = topic
            
            task.save()
            self.log_success(f"Обновлено задание: {task.get_short_uuid()}")
            
        except Exception as e:
            self.log_error(f"Ошибка обновления задания: {e}", e)

    def _find_or_create_subtopic(self, subtopic_data: Any, topic: Topic) -> Optional[SubTopic]:
        """Поиск или создание подтемы"""
        if not subtopic_data or not topic:
            return None
        
        subtopic_name = subtopic_data if isinstance(subtopic_data, str) else subtopic_data.get('name')
        if not subtopic_name:
            return None
        
        # Поиск существующей подтемы
        existing_subtopic = SubTopic.objects.filter(topic=topic, name=subtopic_name).first()
        if existing_subtopic:
            return existing_subtopic
        
        # Создание новой подтемы если разрешено
        if self.create_missing:
            try:
                subtopic = SubTopic.objects.create(
                    topic=topic,
                    name=subtopic_name,
                    description=subtopic_data.get('description', '') if isinstance(subtopic_data, dict) else '',
                    order=subtopic_data.get('order', 1) if isinstance(subtopic_data, dict) else 1
                )
                self.log_success(f"Создана подтема: {subtopic_name}")
                return subtopic
            except Exception as e:
                self.log_error(f"Ошибка создания подтемы: {e}", e)
        
        return None

