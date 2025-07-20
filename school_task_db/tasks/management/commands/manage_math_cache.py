"""Команда управления кэшем математических формул"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from tasks.utils import math_status_cache
from tasks.models import Task

class Command(BaseCommand):
    help = 'Управление кэшем статуса математических формул'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['stats', 'refresh', 'clear', 'warmup'],
            default='stats',
            help='Действие с кэшем: stats (статистика), refresh (обновить), clear (очистить), warmup (прогрев)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Размер батча для обработки заданий'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительное выполнение действия'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'stats':
            self.show_cache_stats()
        
        elif action == 'refresh':
            self.refresh_cache(options['force'])
        
        elif action == 'clear':
            self.clear_cache()
        
        elif action == 'warmup':
            self.warmup_cache(options['batch_size'])
    
    def show_cache_stats(self):
        """Показывает статистику кэша"""
        self.stdout.write(self.style.SUCCESS('📊 Статистика кэша математических формул:'))
        
        stats = math_status_cache.get_cache_stats()
        
        self.stdout.write(f"  Основной кэш: {'✅' if stats['all_status_cached'] else '❌'}")
        self.stdout.write(f"  Задания с формулами: {'✅' if stats['with_math_cached'] else '❌'}")
        self.stdout.write(f"  Задания с ошибками: {'✅' if stats['with_errors_cached'] else '❌'}")
        
        if stats['with_math_cached']:
            self.stdout.write(f"  📐 Всего заданий с формулами: {stats['total_with_math']}")
            self.stdout.write(f"  ❌ Заданий с ошибками в формулах: {stats['total_with_errors']}")
        
        # Статистика по отдельным заданиям
        total_tasks = Task.objects.count()
        if total_tasks > 0:
            # Проверяем сколько заданий закэшировано индивидуально
            cached_tasks = 0
            for task_id in Task.objects.values_list('id', flat=True)[:100]:  # Проверяем первые 100
                cache_key = math_status_cache.get_task_cache_key(task_id)
                if cache.get(cache_key) is not None:
                    cached_tasks += 1
            
            self.stdout.write(f"  📝 Всего заданий в базе: {total_tasks}")
            self.stdout.write(f"  🗄️ Индивидуально закэшировано (выборка): {cached_tasks}/100")
    
    def refresh_cache(self, force=False):
        """Обновляет кэш"""
        if not force:
            confirm = input("Обновить кэш для всех заданий? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("Операция отменена")
                return
        
        self.stdout.write("🔄 Обновление кэша...")
        
        try:
            stats = math_status_cache.refresh_cache()
            
            self.stdout.write(self.style.SUCCESS("✅ Кэш успешно обновлен!"))
            self.stdout.write(f"  📐 Заданий с формулами: {len(stats['with_math'])}")
            self.stdout.write(f"  ❌ Заданий с ошибками: {len(stats['with_errors'])}")
            self.stdout.write(f"  ⚠️ Заданий с предупреждениями: {len(stats['with_warnings'])}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка обновления кэша: {e}"))
    
    def clear_cache(self):
        """Очищает кэш"""
        confirm = input("Очистить весь кэш математических формул? [y/N]: ")
        if confirm.lower() != 'y':
            self.stdout.write("Операция отменена")
            return
        
        math_status_cache.invalidate_all_cache()
        self.stdout.write(self.style.SUCCESS("✅ Кэш очищен"))
    
    def warmup_cache(self, batch_size):
        """Прогревает кэш для всех заданий"""
        self.stdout.write(f"🔥 Прогрев кэша (батч: {batch_size})...")
        
        total_tasks = Task.objects.count()
        processed = 0
        
        for offset in range(0, total_tasks, batch_size):
            tasks_batch = Task.objects.all()[offset:offset + batch_size]
            
            for task in tasks_batch:
                math_status_cache.get_task_math_status(task)
                processed += 1
            
            # Показываем прогресс
            if processed % (batch_size * 5) == 0:
                self.stdout.write(f"  Обработано: {processed}/{total_tasks}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Прогрев завершен! Обработано {processed} заданий"))
