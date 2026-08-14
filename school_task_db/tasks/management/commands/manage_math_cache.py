"""Команда управления кэшем математических формул"""

from django.core.management.base import BaseCommand

from infrastructure.services.task_math_status_cache import (
    task_math_status_cache,
)


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
        
        stats = task_math_status_cache.get_cache_stats()
        
        self.stdout.write(f"  Основной кэш: {'✅' if stats.all_status_cached else '❌'}")
        self.stdout.write(f"  Задания с формулами: {'✅' if stats.with_math_cached else '❌'}")
        self.stdout.write(f"  Задания с ошибками: {'✅' if stats.with_errors_cached else '❌'}")
        
        if stats.with_math_cached:
            self.stdout.write(f"  📐 Всего заданий с формулами: {stats.total_with_math}")
            self.stdout.write(f"  ❌ Заданий с ошибками в формулах: {stats.total_with_errors}")
        
        inventory = task_math_status_cache.get_cache_inventory()
        if inventory['total_tasks'] > 0:
            self.stdout.write(
                f"  📝 Всего заданий в базе: {inventory['total_tasks']}"
            )
            self.stdout.write(
                "  🗄️ Индивидуально закэшировано (выборка): "
                f"{inventory['cached_in_sample']}/{inventory['sample_size']}"
            )
    
    def refresh_cache(self, force=False):
        """Обновляет кэш"""
        if not force:
            confirm = input("Обновить кэш для всех заданий? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("Операция отменена")
                return
        
        self.stdout.write("🔄 Обновление кэша...")
        
        try:
            stats = task_math_status_cache.refresh_cache()
            
            self.stdout.write(self.style.SUCCESS("✅ Кэш успешно обновлен!"))
            self.stdout.write(f"  📐 Заданий с формулами: {len(stats.with_math)}")
            self.stdout.write(f"  ❌ Заданий с ошибками: {len(stats.with_errors)}")
            self.stdout.write(f"  ⚠️ Заданий с предупреждениями: {len(stats.with_warnings)}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка обновления кэша: {e}"))
    
    def clear_cache(self):
        """Очищает кэш"""
        confirm = input("Очистить весь кэш математических формул? [y/N]: ")
        if confirm.lower() != 'y':
            self.stdout.write("Операция отменена")
            return
        
        task_math_status_cache.clear_cache()
        self.stdout.write(self.style.SUCCESS("✅ Кэш очищен"))
    
    def warmup_cache(self, batch_size):
        """Прогревает кэш для всех заданий"""
        self.stdout.write(f"🔥 Прогрев кэша (батч: {batch_size})...")
        
        processed = task_math_status_cache.warmup_cache(batch_size=batch_size)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Прогрев завершен! Обработано {processed} заданий"))
