"""
Базовые классы для системы импорта JSON данных
"""
import uuid
from typing import Any, Dict, Optional

from core_logic.value_objects.task_import import validate_task_import_mode
from infrastructure.repositories.django_uuid_lookup import (
    get_unambiguous_by_uuid,
)


class ImportStats:
    """Статистика импорта"""
    
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.skipped = 0
        self.created_by_type = {}
        self.updated_by_type = {}
        self.skipped_by_type = {}
        self._recorded_operations = set()
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

    def record_created(self, object_type: str, object_id=''):
        self._record('created', object_type, object_id)

    def record_updated(self, object_type: str, object_id=''):
        self._record('updated', object_type, object_id)

    def record_skipped(self, object_type: str, object_id=''):
        self._record('skipped', object_type, object_id)

    def count(self, action: str, object_type: str) -> int:
        return getattr(self, f'{action}_by_type').get(object_type, 0)

    def _record(self, action: str, object_type: str, object_id):
        operation_key = (action, object_type, str(object_id))
        if object_id and operation_key in self._recorded_operations:
            return
        if object_id:
            self._recorded_operations.add(operation_key)
        setattr(self, action, getattr(self, action) + 1)
        counts = getattr(self, f'{action}_by_type')
        counts[object_type] = counts.get(object_type, 0) + 1
    
class BaseImporter:
    """Базовый класс для всех импортеров"""
    
    def __init__(self, 
                 mode: str = 'update',
                 dry_run: bool = False,
                 verbose: bool = False,
                 create_missing: bool = True,
                 output=None):
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
        self.output = output
        self.stats = ImportStats()
        
        # Кэш для избежания повторных запросов
        self._cache = {}

    def _write(self, message: str = ''):
        if self.output is not None:
            self.output(message)
        else:
            print(message)
    
    def validate_mode(self):
        """Валидация режима импорта"""
        validate_task_import_mode(self.mode)
    
    def log_info(self, message: str, indent: int = 0):
        """Логирование информационных сообщений"""
        if self.verbose:
            prefix = "  " * indent
            self._write(f"{prefix}{message}")
    
    def log_warning(self, message: str, context: Optional[Dict] = None):
        """Логирование предупреждений"""
        self._write(f"  ⚠️ {message}")
        self.stats.add_warning(message, context)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, context: Optional[Dict] = None):
        """Логирование ошибок"""
        self._write(f"  ❌ {message}")
        if exception and self.verbose:
            self._write(f"     Детали: {str(exception)}")
        self.stats.add_error(message, exception, context)
    
    def log_success(self, message: str):
        """Логирование успешных операций"""
        if self.verbose:
            self._write(f"  ✅ {message}")
    
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
            obj = get_unambiguous_by_uuid(model_class, uuid_str)
            if obj is not None:
                self._cache[cache_key] = obj
            return obj
        except Exception as e:
            self.log_error(f"Ошибка поиска {model_class.__name__} с UUID {uuid_str[-8:]}: {e}")
            return None
    
    def should_create_object(
        self,
        existing_obj,
        data: Dict[str, Any],
        object_type: str,
    ) -> bool:
        """Определяет нужно ли создавать объект в зависимости от режима"""
        if not existing_obj:
            return True
        
        if self.mode == 'strict':
            raise ValueError(
                'Объект с UUID '
                f"{data.get('id', 'unknown')[-8:]} уже существует "
                'в strict режиме',
            )
        elif self.mode == 'skip':
            self.stats.record_skipped(object_type, existing_obj.pk)
            return False
        elif self.mode == 'update':
            return False  # Будем обновлять существующий
        
        return True
    
class ImportContext:
    """Контекст импорта для передачи данных между импортерами"""
    
    def __init__(self):
        self.imported_topics = {}      # uuid -> Topic
        self.imported_subtopics = {}   # uuid -> SubTopic
        self.imported_groups = {}      # uuid -> AnalogGroup  
        self.imported_tasks = {}       # uuid -> Task
        self.created_dependencies = {} # тип -> список созданных объектов
        self.preview_summary = {}
    
    def add_topic(self, uuid_str: str, topic):
        self.imported_topics[uuid_str] = topic
    
    def add_group(self, uuid_str: str, group):
        self.imported_groups[uuid_str] = group

    def add_subtopic(self, uuid_str: str, subtopic):
        self.imported_subtopics[uuid_str] = subtopic
    
    def add_task(self, uuid_str: str, task):
        self.imported_tasks[uuid_str] = task
    
    def get_stats_summary(self) -> Dict[str, int]:
        return {
            'topics': len(self.imported_topics),
            'subtopics': len(self.imported_subtopics),
            'groups': len(self.imported_groups),
            'tasks': len(self.imported_tasks)
        }
