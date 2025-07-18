"""Универсальная команда для генерации LaTeX документов"""

from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

from latex_generator.generators.registry import registry

class Command(BaseCommand):
    help = 'Универсальная генерация LaTeX документов'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'type', 
            choices=registry.get_available_types(),
            help='Тип документа для генерации'
        )
        parser.add_argument('object_id', type=int, help='ID объекта для генерации')
        parser.add_argument(
            '--format',
            choices=['latex', 'pdf'],
            default='pdf',
            help='Формат вывода: latex или pdf'
        )
        parser.add_argument(
            '--output-dir',
            default='latex_output',
            help='Папка для сохранения файлов'
        )
        parser.add_argument(
            '--with-answers',
            action='store_true',
            help='Включить ответы (для работ)'
        )
    
    def handle(self, *args, **options):
        doc_type = options['type']
        object_id = options['object_id']
        output_format = options['format']
        output_dir = Path(options['output_dir'])
        with_answers = options['with_answers']
        
        # Получаем класс генератора
        generator_class = registry.get_generator(doc_type)
        
        # Получаем объект для генерации
        try:
            model_class = self._get_model_class(doc_type)
            obj = model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            raise CommandError(f'{doc_type.title()} с ID {object_id} не найден')
        
        # Создаем генератор
        generator = generator_class(output_dir)
        
        # Выводим информацию
        self.stdout.write(f'🚀 Генерация {doc_type} для: {obj}')
        if doc_type == 'work':
            # ИСПРАВЛЕНО: variants -> variant_set
            variants_count = obj.variant_set.count()
            if variants_count == 0:
                raise CommandError('У работы нет вариантов. Сначала сгенерируйте варианты.')
            self.stdout.write(f'📋 Найдено вариантов: {variants_count}')
        
        # Генерируем документ
        try:
            if doc_type == 'work' and with_answers:
                files = generator.generate_with_answers(obj, output_format)
            else:
                files = generator.generate(obj, output_format)
            
            self.stdout.write(
                self.style.SUCCESS(f'🎉 Готово! Создано файлов: {len(files)}')
            )
            
            for file_path in files:
                self.stdout.write(f'  📄 {file_path}')
                
        except Exception as e:
            raise CommandError(f'Ошибка при генерации: {e}')
    
    def _get_model_class(self, doc_type):
        """Получить класс модели по типу документа"""
        model_mapping = {
            'work': 'works.Work',
            # В будущем добавим:
            # 'report': 'reports.Report',
        }
        
        if doc_type not in model_mapping:
            raise CommandError(f'Неизвестный тип документа: {doc_type}')
        
        app_label, model_name = model_mapping[doc_type].split('.')
        return apps.get_model(app_label, model_name)
