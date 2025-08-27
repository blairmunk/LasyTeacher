"""
Экспорт заданий в JSON для тестирования импорта
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime

from tasks.models import Task
from task_groups.models import AnalogGroup, TaskGroup  
from curriculum.models import Topic

class Command(BaseCommand):
    help = 'Экспорт заданий в JSON формат'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='Выходной JSON файл')
        parser.add_argument('--include-groups', action='store_true', help='Включить группы аналогов')
        parser.add_argument('--include-topics', action='store_true', help='Включить темы')
        parser.add_argument('--filter-subject', type=str, help='Фильтр по предмету')
        parser.add_argument('--filter-grade', type=int, help='Фильтр по классу')
        parser.add_argument('--limit', type=int, help='Ограничить количество заданий')

    def handle(self, *args, **options):
        print("📤 ЭКСПОРТ ЗАДАНИЙ В JSON:")
        
        # Базовый queryset заданий
        tasks_qs = Task.objects.select_related('topic', 'subtopic').prefetch_related('taskgroup_set__group')
        
        # Применяем фильтры
        if options['filter_subject']:
            tasks_qs = tasks_qs.filter(topic__subject=options['filter_subject'])
            print(f"  📚 Фильтр по предмету: {options['filter_subject']}")
        
        if options['filter_grade']:
            tasks_qs = tasks_qs.filter(topic__grade_level=options['filter_grade'])
            print(f"  🎓 Фильтр по классу: {options['filter_grade']}")
        
        if options['limit']:
            tasks_qs = tasks_qs[:options['limit']]
            print(f"  📊 Ограничение: {options['limit']} заданий")
        
        tasks = list(tasks_qs)
        print(f"  📝 Заданий для экспорта: {len(tasks)}")
        
        # Собираем связанные данные
        used_groups = set()
        used_topics = set()
        
        for task in tasks:
            if task.topic:
                used_topics.add(task.topic)
            
            for task_group in task.taskgroup_set.all():
                used_groups.add(task_group.group)
        
        print(f"  📋 Связанных групп: {len(used_groups)}")
        print(f"  📚 Связанных тем: {len(used_topics)}")
        
        # Создаем JSON структуру
        export_data = {
            "format_version": "1.0",
            "metadata": {
                "description": f"Экспорт заданий из базы данных",
                "created_at": datetime.now().isoformat(),
                "filters": {
                    "subject": options.get('filter_subject'),
                    "grade_level": options.get('filter_grade'),
                    "limit": options.get('limit')
                },
                "totals": {
                    "tasks": len(tasks),
                    "groups": len(used_groups),
                    "topics": len(used_topics)
                }
            }
        }
        
        # Экспорт тем
        if options['include_topics'] and used_topics:
            export_data["topics"] = []
            for topic in used_topics:
                export_data["topics"].append({
                    "name": topic.name,
                    "subject": topic.subject,
                    "grade_level": topic.grade_level,
                    "section": topic.section,
                    "description": topic.description
                })
        
        # Экспорт групп аналогов
        if options['include_groups'] and used_groups:
            export_data["analog_groups"] = []
            for group in used_groups:
                export_data["analog_groups"].append({
                    "id": str(group.id),
                    "name": group.name,
                    "description": group.description
                })
        
        # Экспорт заданий
        export_data["tasks"] = []
        for task in tasks:
            task_data = {
                "id": str(task.id),
                "text": task.text,
                "answer": task.answer,
                "short_solution": task.short_solution,
                "full_solution": task.full_solution,
                "hint": task.hint,
                "instruction": task.instruction,
                "content_element": task.content_element,
                "requirement_element": task.requirement_element,
                "task_type": task.task_type,
                "difficulty": task.difficulty,
                "cognitive_level": task.cognitive_level,
                "estimated_time": task.estimated_time
            }
            
            # Добавляем тему
            if task.topic:
                task_data["topic"] = {
                    "name": task.topic.name,
                    "subject": task.topic.subject,
                    "grade_level": task.topic.grade_level
                }
            
            # Добавляем подтему
            if task.subtopic:
                task_data["subtopic"] = {
                    "name": task.subtopic.name
                }
            
            # Добавляем группы
            groups = [str(tg.group.id) for tg in task.taskgroup_set.all()]
            if groups:
                task_data["groups"] = groups
            
            export_data["tasks"].append(task_data)
        
        # Сохраняем JSON
        output_path = Path(options['output_file'])
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
            
            print(f"✅ Экспорт завершен: {output_path}")
            print(f"📊 Размер файла: {output_path.stat().st_size / 1024:.1f} KB")
            
        except Exception as e:
            raise CommandError(f"Ошибка записи файла: {e}")
