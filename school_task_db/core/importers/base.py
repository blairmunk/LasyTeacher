"""
Базовые классы для системы импорта JSON данных
"""
import uuid
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from django.db import transaction, IntegrityError
from django.core.management.base import CommandError

class ImportStats:
    """Статистика импорта"""
    
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.skipped = 0
        self.errors = 0
        self.warnings = []
        self.error_details = []
    
    def add_warning(self, message: str, context: Optional[Dict] = None):
        self.warnings.append({
            'message': message,
            'context': context or {},
            'timestamp': str(uuid.uuid4())  # Для отладки
        })
    
    def add_error(self, message: str, exception: Optional[Exception] = None, context: Optional[Dict] = None):
        self.errors += 1
        self.error_details.append({
            'message': message,
            'exception': str(exception) if exception else None,
            'context': context or {},
            'timestamp': str(uuid.uuid4())
        })
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'created': self.created,
            'updated': self.updated,
            'skipped': self.skipped,
            'errors': self.errors,
            'warnings_count': len(self.warnings),
            'success_rate': self.get_success_rate()
        }
    
    def get_success_rate(self) -> float:
        total = self.created + self.updated + self.skipped + self.errors
        if total == 0:
            return 100.0
        successful = self.created + self.updated + self.skipped
        return (successful / total) * 100.0

class BaseImporter:
    """Базовый класс для всех импортеров"""
    
    def __init__(self, 
                 mode: str = 'update',
                 dry_run: bool = False,
                 verbose: bool = False,
                 create_missing: bool = True):
        """
        Args:
            mode: Режим импорта (strict/update/skip)
            dry_run: Предварительный просмотр без изменений
            verbose: Подробный вывод
            create_missing: Создавать отсутствующие зависимости
        """
        self.mode = mode
        self.dry_run = dry_run
        self.verbose = verbose
        self.create_missing = create_missing
        self.stats = ImportStats()
        
        # Кэш для избежания повторных запросов
        self._cache = {}
    
    def validate_mode(self):
        """Валидация режима импорта"""
        valid_modes = ['strict', 'update', 'skip']
        if self.mode not in valid_modes:
            raise CommandError(f"Неверный режим импорта: {self.mode}. Доступны: {', '.join(valid_modes)}")
    
    def log_info(self, message: str, indent: int = 0):
        """Логирование информационных сообщений"""
        if self.verbose:
            prefix = "  " * indent
            print(f"{prefix}{message}")
    
    def log_warning(self, message: str, context: Optional[Dict] = None):
        """Логирование предупреждений"""
        print(f"  ⚠️ {message}")
        self.stats.add_warning(message, context)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, context: Optional[Dict] = None):
        """Логирование ошибок"""
        print(f"  ❌ {message}")
        if exception and self.verbose:
            print(f"     Детали: {str(exception)}")
        self.stats.add_error(message, exception, context)
    
    def log_success(self, message: str):
        """Логирование успешных операций"""
        if self.verbose:
            print(f"  ✅ {message}")
    
    def generate_uuid_if_missing(self, data: Dict[str, Any], field_name: str = 'id') -> str:
        """Генерирует UUID если отсутствует"""
        if field_name not in data or not data[field_name]:
            data[field_name] = str(uuid.uuid4())
            self.log_info(f"Генерируем UUID: {data[field_name][-8:]}")
        return data[field_name]
    
    def safe_get_by_uuid(self, model_class, uuid_str: str):
        """Безопасное получение объекта по UUID с кэшированием"""
        cache_key = f"{model_class.__name__}:{uuid_str}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            obj = model_class.get_by_uuid(uuid_str)
            self._cache[cache_key] = obj
            return obj
        except Exception as e:
            self.log_error(f"Ошибка поиска {model_class.__name__} с UUID {uuid_str[-8:]}: {e}")
            return None
    
    def clear_cache(self):
        """Очистка кэша"""
        self._cache.clear()
    
    def should_create_object(self, existing_obj, data: Dict[str, Any]) -> bool:
        """Определяет нужно ли создавать объект в зависимости от режима"""
        if not existing_obj:
            return True
        
        if self.mode == 'strict':
            raise CommandError(f"Объект с UUID {data.get('id', 'unknown')[-8:]} уже существует в strict режиме")
        elif self.mode == 'skip':
            self.stats.skipped += 1
            return False
        elif self.mode == 'update':
            return False  # Будем обновлять существующий
        
        return True
    
    def print_import_summary(self):
        """Печать итогового резюме импорта"""
        summary = self.stats.get_summary()
        
        print("\n📊 ИТОГИ ИМПОРТА:")
        print(f"  ✅ Создано: {summary['created']}")
        print(f"  ✏️ Обновлено: {summary['updated']}")
        print(f"  ⏭️ Пропущено: {summary['skipped']}")
        print(f"  ❌ Ошибок: {summary['errors']}")
        print(f"  ⚠️ Предупреждений: {summary['warnings_count']}")
        print(f"  🎯 Успешность: {summary['success_rate']:.1f}%")
        
        # Детали ошибок
        if self.stats.errors > 0 and self.verbose:
            print("\n❌ ДЕТАЛИ ОШИБОК:")
            for error in self.stats.error_details[:5]:  # Показываем первые 5
                print(f"  • {error['message']}")
                if error['exception']:
                    print(f"    Исключение: {error['exception']}")
        
        # Предупреждения
        if len(self.stats.warnings) > 0 and self.verbose:
            print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            for warning in self.stats.warnings[:5]:  # Показываем первые 5
                print(f"  • {warning['message']}")

class ImportContext:
    """Контекст импорта для передачи данных между импортерами"""
    
    def __init__(self):
        self.imported_topics = {}      # uuid -> Topic
        self.imported_groups = {}      # uuid -> AnalogGroup  
        self.imported_tasks = {}       # uuid -> Task
        self.created_dependencies = {} # тип -> список созданных объектов
    
    def add_topic(self, uuid_str: str, topic):
        self.imported_topics[uuid_str] = topic
    
    def add_group(self, uuid_str: str, group):
        self.imported_groups[uuid_str] = group
    
    def add_task(self, uuid_str: str, task):
        self.imported_tasks[uuid_str] = task
    
    def get_stats_summary(self) -> Dict[str, int]:
        return {
            'topics': len(self.imported_topics),
            'groups': len(self.imported_groups),
            'tasks': len(self.imported_tasks)
        }

def validate_json_structure(data: Dict[str, Any], required_fields: List[str], context: str = "") -> bool:
    """Валидация базовой структуры JSON"""
    missing_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        raise CommandError(f"Отсутствуют обязательные поля в {context}: {', '.join(missing_fields)}")
    
    return True
