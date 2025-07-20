"""Утилиты для кэширования статуса математических формул в заданиях"""

import logging
from typing import Dict, Set, List, Optional
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from latex_generator.utils.formula_utils import formula_processor

logger = logging.getLogger(__name__)

class MathStatusCache:
    """Кэш для статуса математических формул в заданиях"""
    
    # Ключи кэша
    CACHE_KEY_ALL_MATH = 'tasks_math_status_all'
    CACHE_KEY_WITH_MATH = 'tasks_with_math_ids'
    CACHE_KEY_WITH_ERRORS = 'tasks_with_errors_ids'
    CACHE_KEY_TASK_PREFIX = 'task_math_status_'
    
    # Время жизни кэша (1 час)
    CACHE_TIMEOUT = 3600
    
    # Время жизни кэша для отдельных заданий (24 часа)
    TASK_CACHE_TIMEOUT = 86400
    
    @classmethod
    def get_task_cache_key(cls, task_id: int) -> str:
        """Генерирует ключ кэша для отдельного задания"""
        return f"{cls.CACHE_KEY_TASK_PREFIX}{task_id}"
    
    @classmethod
    def get_task_math_status(cls, task) -> Dict[str, any]:
        """Получает статус формул для отдельного задания с кэшированием"""
        cache_key = cls.get_task_cache_key(task.id)
        cached_status = cache.get(cache_key)
        
        if cached_status is not None:
            return cached_status
        
        # Вычисляем статус формул
        try:
            has_math = formula_processor.has_math(task.text)
            
            if has_math:
                processed = formula_processor.process_text_safe(task.text)
                has_errors = processed.get('has_errors', False)
                has_warnings = processed.get('has_warnings', False)
                error_count = len(processed.get('errors', []))
                warning_count = len(processed.get('warnings', []))
            else:
                has_errors = False
                has_warnings = False
                error_count = 0
                warning_count = 0
            
            status = {
                'has_math': has_math,
                'has_errors': has_errors,
                'has_warnings': has_warnings,
                'error_count': error_count,
                'warning_count': warning_count,
                'task_id': task.id,
                'last_updated': task.updated_at.isoformat() if hasattr(task, 'updated_at') else None
            }
            
            # Кэшируем результат
            cache.set(cache_key, status, cls.TASK_CACHE_TIMEOUT)
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении статуса формул для задания {task.id}: {e}")
            # Возвращаем безопасные значения по умолчанию
            return {
                'has_math': False,
                'has_errors': False,
                'has_warnings': False,
                'error_count': 0,
                'warning_count': 0,
                'task_id': task.id,
                'last_updated': None
            }
    
    @classmethod
    def get_all_tasks_math_status(cls, force_refresh: bool = False) -> Dict[str, Set[int]]:
        """Получает статус формул для всех заданий с кэшированием"""
        if not force_refresh:
            cached_data = cache.get(cls.CACHE_KEY_ALL_MATH)
            if cached_data is not None:
                logger.debug("Используем кэшированные данные статуса формул")
                return cached_data
        
        logger.info("Вычисляем статус формул для всех заданий...")
        
        from tasks.models import Task
        
        result = {
            'with_math': set(),
            'with_errors': set(),
            'with_warnings': set(),
        }
        
        # Обрабатываем задания батчами для экономии памяти
        batch_size = 100
        total_tasks = Task.objects.count()
        processed_count = 0
        
        for offset in range(0, total_tasks, batch_size):
            tasks_batch = Task.objects.all()[offset:offset + batch_size]
            
            for task in tasks_batch:
                status = cls.get_task_math_status(task)
                
                if status['has_math']:
                    result['with_math'].add(task.id)
                
                if status['has_errors']:
                    result['with_errors'].add(task.id)
                
                if status['has_warnings']:
                    result['with_warnings'].add(task.id)
                
                processed_count += 1
            
            # Показываем прогресс для больших объемов данных
            if total_tasks > 1000 and processed_count % 500 == 0:
                logger.info(f"Обработано заданий: {processed_count}/{total_tasks}")
        
        logger.info(f"Завершена обработка {processed_count} заданий")
        logger.info(f"С формулами: {len(result['with_math'])}, "
                   f"с ошибками: {len(result['with_errors'])}, "
                   f"с предупреждениями: {len(result['with_warnings'])}")
        
        # Кэшируем результат
        cache.set(cls.CACHE_KEY_ALL_MATH, result, cls.CACHE_TIMEOUT)
        
        # Также сохраняем отдельные списки для быстрого доступа
        cache.set(cls.CACHE_KEY_WITH_MATH, result['with_math'], cls.CACHE_TIMEOUT)
        cache.set(cls.CACHE_KEY_WITH_ERRORS, result['with_errors'], cls.CACHE_TIMEOUT)
        
        return result
    
    @classmethod
    def get_tasks_with_math_ids(cls) -> Set[int]:
        """Получает ID заданий с формулами"""
        cached_ids = cache.get(cls.CACHE_KEY_WITH_MATH)
        if cached_ids is not None:
            return cached_ids
        
        # Если кэш отдельных ID не найден, получаем полные данные
        all_status = cls.get_all_tasks_math_status()
        return all_status['with_math']
    
    @classmethod
    def get_tasks_with_errors_ids(cls) -> Set[int]:
        """Получает ID заданий с ошибками в формулах"""
        cached_ids = cache.get(cls.CACHE_KEY_WITH_ERRORS)
        if cached_ids is not None:
            return cached_ids
        
        # Если кэш отдельных ID не найден, получаем полные данные
        all_status = cls.get_all_tasks_math_status()
        return all_status['with_errors']
    
    @classmethod
    def invalidate_task_cache(cls, task_id: int):
        """Инвалидирует кэш для конкретного задания"""
        cache_key = cls.get_task_cache_key(task_id)
        cache.delete(cache_key)
        logger.debug(f"Инвалидирован кэш для задания {task_id}")
    
    @classmethod
    def invalidate_all_cache(cls):
        """Инвалидирует весь кэш статуса формул"""
        keys_to_delete = [
            cls.CACHE_KEY_ALL_MATH,
            cls.CACHE_KEY_WITH_MATH,
            cls.CACHE_KEY_WITH_ERRORS,
        ]
        
        cache.delete_many(keys_to_delete)
        logger.info("Инвалидирован весь кэш статуса формул")
    
    @classmethod
    def refresh_cache(cls):
        """Принудительно обновляет кэш"""
        logger.info("Принудительное обновление кэша статуса формул")
        return cls.get_all_tasks_math_status(force_refresh=True)
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, any]:
        """Получает статистику кэша"""
        all_status = cache.get(cls.CACHE_KEY_ALL_MATH)
        with_math = cache.get(cls.CACHE_KEY_WITH_MATH)
        with_errors = cache.get(cls.CACHE_KEY_WITH_ERRORS)
        
        return {
            'all_status_cached': all_status is not None,
            'with_math_cached': with_math is not None,
            'with_errors_cached': with_errors is not None,
            'total_with_math': len(with_math) if with_math else 0,
            'total_with_errors': len(with_errors) if with_errors else 0,
        }

# Создаем глобальный экземпляр
math_status_cache = MathStatusCache()

# Сигналы для автоматической инвалидации кэша
@receiver(post_save, sender='tasks.Task')
def invalidate_task_math_cache_on_save(sender, instance, **kwargs):
    """Инвалидирует кэш при сохранении задания"""
    math_status_cache.invalidate_task_cache(instance.id)
    
    # Если это новое задание или изменился текст, инвалидируем общий кэш
    if kwargs.get('created') or hasattr(instance, '_text_changed'):
        math_status_cache.invalidate_all_cache()

@receiver(post_delete, sender='tasks.Task')
def invalidate_task_math_cache_on_delete(sender, instance, **kwargs):
    """Инвалидирует кэш при удалении задания"""
    math_status_cache.invalidate_task_cache(instance.id)
    math_status_cache.invalidate_all_cache()
