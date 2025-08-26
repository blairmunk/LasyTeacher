"""Команда для конвертации HTML в PDF"""

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Конвертирует HTML файлы в PDF через Playwright'

    def add_arguments(self, parser):
        # HTML файл или директория
        parser.add_argument(
            'input_path',
            help='Путь к HTML файлу или директории с HTML файлами'
        )
        
        # Выходной путь (опционально)
        parser.add_argument(
            '--output-dir',
            default='pdf_output',
            help='Директория для сохранения PDF файлов (по умолчанию: pdf_output)'
        )
        
        # Формат страницы
        parser.add_argument(
            '--format',
            choices=['A4', 'A3', 'Letter', 'Legal'],
            default='A4',
            help='Формат страницы (по умолчанию: A4)'
        )
        
        # Поля
        parser.add_argument(
            '--margin',
            default='1cm',
            help='Поля страницы (по умолчанию: 1cm)'
        )
        
        # Фоновые изображения
        parser.add_argument(
            '--no-background',
            action='store_true',
            help='Не печатать фоновые изображения и цвета'
        )
        
        # MathJax
        parser.add_argument(
            '--skip-mathjax',
            action='store_true',
            help='Не ждать загрузки MathJax'
        )

    def handle(self, *args, **options):
        input_path = Path(options['input_path'])
        output_dir = options['output_dir']
        
        if not input_path.exists():
            raise CommandError(f"Путь не существует: {input_path}")
        
        try:
            from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator
            from pdf_generator.utils import get_output_pdf_path, batch_html_to_pdf_paths
            
            # Настраиваем генератор
            generator_options = {
                'format': options['format'],
                'print_background': not options['no_background'],
                'wait_for_mathjax': not options['skip_mathjax'],
            }
            
            # Парсим margin
            margin_value = options['margin']
            generator_options['margin'] = {
                'top': margin_value, 'right': margin_value, 
                'bottom': margin_value, 'left': margin_value
            }
            
            generator = HtmlToPdfGenerator(**generator_options)
            
            if input_path.is_file():
                # Обрабатываем один файл
                if not input_path.suffix.lower() == '.html':
                    raise CommandError(f"Файл должен иметь расширение .html: {input_path}")
                
                output_path = get_output_pdf_path(input_path, output_dir)
                
                self.stdout.write(f"🔄 Конвертируем: {input_path.name}")
                result_path = generator.generate_pdf(input_path, output_path)
                
                # Проверяем результат
                if result_path.exists():
                    file_size = result_path.stat().st_size / 1024  # KB
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ PDF создан: {result_path} ({file_size:.1f} KB)"
                        )
                    )
                else:
                    raise CommandError("PDF файл не был создан")
            
            elif input_path.is_dir():
                # Обрабатываем директорию
                html_files = list(input_path.glob('*.html'))
                
                if not html_files:
                    raise CommandError(f"HTML файлы не найдены в директории: {input_path}")
                
                self.stdout.write(f"🔄 Найдено HTML файлов: {len(html_files)}")
                
                # Подготавливаем пары файлов
                file_pairs = batch_html_to_pdf_paths(html_files, output_dir)
                
                if not file_pairs:
                    raise CommandError("Корректные HTML файлы не найдены")
                
                self.stdout.write(f"🔄 Обрабатываем {len(file_pairs)} файлов...")
                
                # Генерируем PDF файлы
                for i, (html_file, pdf_file) in enumerate(file_pairs, 1):
                    self.stdout.write(f"  {i}/{len(file_pairs)}: {html_file.name}")
                    
                    try:
                        result_path = generator.generate_pdf(html_file, pdf_file)
                        file_size = result_path.stat().st_size / 1024  # KB
                        self.stdout.write(f"    ✅ PDF: {pdf_file.name} ({file_size:.1f} KB)")
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"    ❌ Ошибка: {e}")
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f"🎉 Обработка завершена! PDF файлы в: {output_dir}")
                )
        
        except ImportError as e:
            raise CommandError(
                f"Playwright не установлен: {e}. "
                "Выполните: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            logger.error(f"Ошибка конвертации HTML→PDF: {e}")
            raise CommandError(f"Ошибка: {e}")
