"""Команда для генерации HTML документов"""

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Генерирует HTML документы для различных типов объектов'

    def add_arguments(self, parser):
        # Тип объекта для генерации
        parser.add_argument(
            'object_type',
            choices=['work'],
            help='Тип объекта для генерации (work)'
        )
        
        # ID объекта
        parser.add_argument(
            'object_id',
            type=int,
            help='ID объекта для генерации'
        )
        
        # Формат вывода (пока только HTML)
        parser.add_argument(
            '--format',
            choices=['html'],
            default='html',
            help='Формат генерации (по умолчанию: html)'
        )
        
        # С ответами или без
        parser.add_argument(
            '--with-answers',
            action='store_true',
            help='Включить ответы и решения в документ'
        )
        
        # Выходная директория
        parser.add_argument(
            '--output-dir',
            default='html_output',
            help='Директория для сохранения файлов (по умолчанию: html_output)'
        )

    def handle(self, *args, **options):
        object_type = options['object_type']
        object_id = options['object_id']
        output_format = options['format']
        with_answers = options['with_answers']
        output_dir = options['output_dir']

        try:
            # Определяем модель и генератор по типу объекта
            if object_type == 'work':
                Work = apps.get_model('works', 'Work')
                obj = Work.objects.get(id=object_id)
                
                from html_generator.generators.work_generator import WorkHtmlGenerator
                generator = WorkHtmlGenerator(output_dir=output_dir)
                
                self.stdout.write(
                    f"🌐 Генерация {object_type} для: [{obj.get_short_uuid()}] {obj.name}"
                )
                
                # Проверяем количество вариантов
                variants_count = obj.variant_set.count()
                self.stdout.write(f"📋 Найдено вариантов: {variants_count}")
                
                if variants_count == 0:
                    raise CommandError(f"У работы {obj.name} нет вариантов для генерации")
                
                # Генерируем HTML
                if with_answers:
                    files = generator.generate_with_answers(obj)
                else:
                    files = generator.generate(obj)
                
                # Проверяем наличие ошибок формул в контексте
                context = generator.prepare_context(obj)
                
                if context.get('has_formula_errors'):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Работа {obj.name} содержит ошибки в формулах: {context['formula_errors']}"
                        )
                    )
                
                if context.get('has_formula_warnings'):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Работа {obj.name} содержит предупреждения в формулах: {context['formula_warnings']}"
                        )
                    )
            
            else:
                raise CommandError(f"Неподдерживаемый тип объекта: {object_type}")

            # Выводим результат
            self.stdout.write("🎉 Готово! Создано файлов: {}".format(len(files)))
            for file_path in files:
                self.stdout.write(f"  📄 {file_path}")
                
                # Дополнительная информация о HTML файле
                if file_path.endswith('.html'):
                    html_path = Path(file_path)
                    if html_path.exists():
                        file_size = html_path.stat().st_size / 1024  # KB
                        self.stdout.write(f"     Размер: {file_size:.1f} KB")

        except Work.DoesNotExist:
            raise CommandError(f"Работа с ID {object_id} не найдена")
        except Exception as e:
            logger.error(f"Ошибка генерации HTML для {object_type} {object_id}: {e}")
            raise CommandError(f"Ошибка при генерации: {e}")
