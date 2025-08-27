"""
Расширенный анализ изображений с отчетом по пустым позициям
"""
from django.core.management.base import BaseCommand
from tasks.models import Task, TaskImage
from django.db.models import Q

class Command(BaseCommand):
    help = 'Анализ изображений заданий с фокусом на отсутствующие позиции'

    def add_arguments(self, parser):
        parser.add_argument('--show-missing', action='store_true', 
                           help='Показать детали изображений без позиций')
        parser.add_argument('--fix-missing', action='store_true',
                           help='Предложить исправление пустых позиций')

    def handle(self, *args, **options):
        print("📊 АНАЛИЗ ИЗОБРАЖЕНИЙ ЗАДАНИЙ:")
        
        total_images = TaskImage.objects.count()
        print(f"  🖼️ Всего изображений: {total_images}")
        
        if total_images == 0:
            print("  ℹ️ Изображений нет")
            return
        
        # Анализ по позициям
        positions = {}
        missing_position_images = []
        
        for image in TaskImage.objects.all():
            if image.position:
                pos = image.position
                positions[pos] = positions.get(pos, 0) + 1
            else:
                positions['MISSING'] = positions.get('MISSING', 0) + 1
                missing_position_images.append(image)
        
        print(f"\n📍 РАСПРЕДЕЛЕНИЕ ПО ПОЗИЦИЯМ:")
        for pos, count in sorted(positions.items()):
            percentage = (count / total_images) * 100
            if pos == 'MISSING':
                display_name = "⚠️ ПОЗИЦИЯ НЕ ЗАДАНА"
                print(f"  {display_name}: {count} ({percentage:.1f}%)")
            else:
                display_name = dict(TaskImage.POSITION_CHOICES).get(pos, pos)
                print(f"  {display_name}: {count} ({percentage:.1f}%)")
        
        # Детальный анализ пропущенных позиций
        missing_count = len(missing_position_images)
        if missing_count > 0:
            print(f"\n🔍 ИЗОБРАЖЕНИЯ БЕЗ ПОЗИЦИИ: {missing_count}")
            
            if options['show_missing']:
                print("\n📝 ДЕТАЛИ:")
                for i, image in enumerate(missing_position_images[:10], 1):
                    task_preview = image.task.text[:40] + "..." if len(image.task.text) > 40 else image.task.text
                    print(f"  {i}. [{image.get_short_uuid()}] {task_preview}")
                    print(f"     Задание: {image.task.topic.name}")
                    print(f"     Файл: {image.image.name}")
                    if image.caption:
                        print(f"     Подпись: {image.caption}")
                    print()
                
                if missing_count > 10:
                    print(f"     ... и еще {missing_count - 10}")
            
            # Предложение автоисправления
            if options['fix_missing']:
                print("\n🔧 ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ:")
                
                # Анализируем подписи для предложения позиций
                suggestions = []
                for image in missing_position_images:
                    suggested_position = self.suggest_position(image)
                    suggestions.append((image, suggested_position))
                
                # Группируем предложения
                by_suggestion = {}
                for image, suggestion in suggestions:
                    if suggestion not in by_suggestion:
                        by_suggestion[suggestion] = []
                    by_suggestion[suggestion].append(image)
                
                for position, images in by_suggestion.items():
                    position_display = dict(TaskImage.POSITION_CHOICES).get(position, position)
                    print(f"  📍 {position_display}: {len(images)} изображений")
                
                # Спрашиваем подтверждение
                if input("\nПрименить предложенные позиции? (y/n): ").lower() == 'y':
                    updated = 0
                    for image, position in suggestions:
                        image.position = position
                        image.save()
                        updated += 1
                    
                    print(f"✅ Обновлено позиций: {updated}")
            
            # Рекомендации
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            print(f"  • Для массового обновления: python manage.py analyze_images --fix-missing")
            print(f"  • Для ручного редактирования перейдите в админ-панель")
            print(f"  • При импорте указывайте position в JSON для избежания пустых позиций")
        else:
            print(f"\n✅ Все изображения имеют заданные позиции")
    
    def suggest_position(self, image):
        """Предлагает позицию на основе анализа изображения и подписи"""
        # Анализируем подпись
        caption = (image.caption or '').lower()
        
        # Ключевые слова для позиций
        if any(word in caption for word in ['график', 'диаграмма', 'схема', 'рисунок']):
            return 'bottom_70'  # Графики обычно снизу
        elif any(word in caption for word in ['портрет', 'фото', 'изображение']):
            return 'right_20'   # Портреты сбоку
        elif 'таблица' in caption:
            return 'bottom_100' # Таблицы на всю ширину
        else:
            return 'bottom_70'  # По умолчанию
