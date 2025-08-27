"""
Валидация JSON файлов перед импортом
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Валидация JSON файлов импорта'

    def add_arguments(self, parser):
        parser.add_argument('json_files', nargs='+', help='JSON файлы для валидации')
        parser.add_argument('--verbose', action='store_true', help='Подробная диагностика')

    def handle(self, *args, **options):
        print("🔍 ВАЛИДАЦИЯ JSON ФАЙЛОВ:")
        
        total_files = len(options['json_files'])
        valid_files = 0
        
        for json_file_path in options['json_files']:
            print(f"\n📄 Проверка: {json_file_path}")
            
            if self.validate_file(json_file_path, options['verbose']):
                valid_files += 1
        
        print(f"\n📊 ИТОГИ ВАЛИДАЦИИ:")
        print(f"  ✅ Валидных файлов: {valid_files}")
        print(f"  ❌ Невалидных файлов: {total_files - valid_files}")
        print(f"  🎯 Успешность: {(valid_files/total_files)*100:.1f}%")

    def validate_file(self, file_path: str, verbose: bool) -> bool:
        """Валидация одного файла"""
        path = Path(file_path)
        
        # Проверка существования файла
        if not path.exists():
            print(f"  ❌ Файл не найден: {file_path}")
            return False
        
        # Проверка JSON синтаксиса
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ❌ Ошибка JSON синтаксиса: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Ошибка чтения файла: {e}")
            return False
        
        # Валидация структуры
        issues = []
        
        # Проверка основных секций
        if 'tasks' not in data:
            issues.append("Отсутствует секция 'tasks'")
        
        # Проверка заданий
        if 'tasks' in data:
            for i, task in enumerate(data['tasks']):
                task_issues = self.validate_task(task, i)
                issues.extend(task_issues)
        
        # Проверка групп
        if 'analog_groups' in data:
            for i, group in enumerate(data['analog_groups']):
                group_issues = self.validate_group(group, i)
                issues.extend(group_issues)
        
        # Вывод результата
        if issues:
            print(f"  ❌ Найдено проблем: {len(issues)}")
            if verbose:
                for issue in issues[:10]:  # Показываем первые 10
                    print(f"    • {issue}")
                if len(issues) > 10:
                    print(f"    ... и еще {len(issues) - 10}")
            return False
        else:
            print(f"  ✅ Файл валиден")
            if verbose:
                tasks_count = len(data.get('tasks', []))
                groups_count = len(data.get('analog_groups', []))
                print(f"    📊 Заданий: {tasks_count}, групп: {groups_count}")
            return True

    def validate_task(self, task: dict, index: int) -> list:
        """Валидация задания"""
        issues = []
        
        # Обязательные поля
        required_fields = ['text']
        for field in required_fields:
            if field not in task or not task[field]:
                issues.append(f"Задание {index}: отсутствует поле '{field}'")
        
        # UUID формат
        if 'id' in task:
            try:
                import uuid
                uuid.UUID(task['id'])
            except ValueError:
                issues.append(f"Задание {index}: некорректный UUID '{task['id']}'")
        
        # Валидация полей
        if 'difficulty' in task:
            try:
                diff = int(task['difficulty'])
                if not (1 <= diff <= 5):
                    issues.append(f"Задание {index}: difficulty должно быть 1-5")
            except (ValueError, TypeError):
                issues.append(f"Задание {index}: difficulty должно быть числом")
        
        return issues

    def validate_group(self, group: dict, index: int) -> list:
        """Валидация группы"""
        issues = []
        
        # Обязательные поля
        if 'name' not in group or not group['name']:
            issues.append(f"Группа {index}: отсутствует имя")
        
        # UUID формат
        if 'id' in group:
            try:
                import uuid
                uuid.UUID(group['id'])
            except ValueError:
                issues.append(f"Группа {index}: некорректный UUID '{group['id']}'")
        
        return issues
