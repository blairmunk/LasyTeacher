"""HTML генератор для работ с поддержкой MathJax и изображений"""

from typing import Dict, Any
from pathlib import Path

from document_generator.utils.formula_utils import formula_processor
from document_generator.utils.file_utils import sanitize_filename
from html_generator.utils.html_specific import html_formula_processor
from document_generator.utils.html_image_utils import prepare_images_for_html, render_task_with_images_html

from .base import BaseHtmlGenerator
import logging

logger = logging.getLogger(__name__)

class WorkHtmlGenerator(BaseHtmlGenerator):
    """Генератор HTML документов для работ с математическими формулами"""
    
    def get_template_name(self) -> str:
        return 'html/work/all_variants.html'
    
    def get_output_filename(self, work) -> str:
        return f"{work.name}_all_variants.html"
    
    def prepare_context(self, work) -> Dict[str, Any]:
        """Подготавливает контекст для работы с обработкой формул"""
        
        variants = work.variant_set.all().order_by('number')
        
        # Подготавливаем данные для каждого варианта
        all_variants_data = []
        document_errors = []
        document_warnings = []
        
        for variant in variants:
            variant_data = self._prepare_variant_context(variant)
            all_variants_data.append(variant_data)
            
            # Собираем ошибки и предупреждения
            document_errors.extend(variant_data.get('errors', []))
            document_warnings.extend(variant_data.get('warnings', []))
        
        # Обрабатываем название работы
        work_name_processed = html_formula_processor.render_for_html_safe(work.name)
        document_errors.extend(work_name_processed['errors'])
        document_warnings.extend(work_name_processed['warnings'])
        
        return {
            'work': work,
            'work_name': work_name_processed['content'],
            'variants': all_variants_data,
            'total_variants': len(all_variants_data),
            'with_answers': getattr(self, '_with_answers', False),
            
            # Информация об ошибках формул
            'has_formula_errors': len(document_errors) > 0,
            'has_formula_warnings': len(document_warnings) > 0,
            'formula_errors': document_errors,
            'formula_warnings': document_warnings,
        }
    
    def _prepare_variant_context(self, variant):
        """Подготавливает контекст для одного варианта с обработкой формул"""
        print(f"🔍 HTML: Обрабатываем вариант {variant.number}")
        
        tasks = variant.tasks.all().order_by('id')
        
        prepared_tasks = []
        variant_errors = []
        variant_warnings = []
        
        # ДОБАВЛЕНО: Получаем конфигурацию контента
        content_config = getattr(self, '_content_config', {})
        include_answers = content_config.get('include_answers', False)
        include_short_solutions = content_config.get('include_short_solutions', False) 
        include_full_solutions = content_config.get('include_full_solutions', False)
        
        print(f"🔍 HTML: Конфигурация контента: answers={include_answers}, short={include_short_solutions}, full={include_full_solutions}")
        
        for i, task in enumerate(tasks, 1):
            print(f"🔍 HTML: Обрабатываем задание {task.id} (номер {i})")
            
            # Обрабатываем текст задания для HTML
            try:
                text_processed = html_formula_processor.render_for_html_safe(task.text)
                
                # ОБНОВЛЕНО: Обрабатываем ответ только если нужно
                if include_answers:
                    answer_processed = html_formula_processor.render_for_html_safe(task.answer or '')
                else:
                    answer_processed = {'content': '', 'errors': [], 'warnings': []}
                    
            except Exception as e:
                print(f"❌ ОШИБКА в HTML обработке формул задания {task.id}: {e}")
                # Fallback - используем исходный текст с HTML экранированием
                text_processed = {'content': html_formula_processor._escape_html(task.text), 'errors': [str(e)], 'warnings': []}
                answer_processed = {'content': '', 'errors': [], 'warnings': []}
            
            # Собираем ошибки и предупреждения
            task_errors = []
            task_warnings = []
            
            task_errors.extend(text_processed['errors'])
            task_errors.extend(answer_processed['errors'])
            task_warnings.extend(text_processed['warnings'])
            task_warnings.extend(answer_processed['warnings'])
            
            # ОБНОВЛЕНО: Обрабатываем дополнительные поля в зависимости от конфигурации
            additional_fields = {}
            
            # Краткие решения
            if include_short_solutions and task.short_solution:
                try:
                    short_processed = html_formula_processor.render_for_html_safe(task.short_solution)
                    additional_fields['short_solution'] = short_processed['content']
                    task_errors.extend(short_processed['errors'])
                    task_warnings.extend(short_processed['warnings'])
                except Exception as e:
                    print(f"❌ ОШИБКА в HTML обработке краткого решения: {e}")
                    additional_fields['short_solution'] = html_formula_processor._escape_html(task.short_solution)
            else:
                additional_fields['short_solution'] = ''
            
            # Полные решения
            if include_full_solutions and task.full_solution:
                try:
                    full_processed = html_formula_processor.render_for_html_safe(task.full_solution)
                    additional_fields['full_solution'] = full_processed['content']
                    task_errors.extend(full_processed['errors'])
                    task_warnings.extend(full_processed['warnings'])
                except Exception as e:
                    print(f"❌ ОШИБКА в HTML обработке полного решения: {e}")
                    additional_fields['full_solution'] = html_formula_processor._escape_html(task.full_solution)
            else:
                additional_fields['full_solution'] = ''
            
            # Подсказки и инструкции (всегда обрабатываем если есть)
            for field_name in ['hint', 'instruction']:
                field_value = getattr(task, field_name, None)
                if field_value:
                    try:
                        processed = html_formula_processor.render_for_html_safe(field_value)
                        additional_fields[field_name] = processed['content']
                        task_errors.extend(processed['errors'])
                        task_warnings.extend(processed['warnings'])
                    except Exception as e:
                        print(f"❌ ОШИБКА в HTML обработке поля {field_name}: {e}")
                        additional_fields[field_name] = html_formula_processor._escape_html(field_value)
                else:
                    additional_fields[field_name] = ''
            
            # Подготавливаем изображения для HTML
            try:
                images_count = task.images.count()
                print(f"🔍 HTML: Задание {task.id}: найдено {images_count} изображений")
                
                if images_count > 0:
                    for img in task.images.all():
                        print(f"🔍 HTML:   Изображение {img.id}: файл={img.image.name}, позиция={img.position}")
                
                # Подготавливаем изображения для HTML
                task_images = prepare_images_for_html(task, self.output_dir)
                print(f"🔍 HTML: После prepare_images_for_html: {len(task_images)} изображений")
                        
            except Exception as e:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при HTML обработке изображений задания {task.id}: {e}")
                task_images = []  # Fallback - без изображений
            
            # Базовые данные задания с обработанными формулами
            task_data = {
                'number': i,
                'task': task,
                'text': text_processed['content'],
                'answer': answer_processed['content'],
                'images': task_images,
                
                # Информация об ошибках формул
                'has_formula_errors': len(task_errors) > 0,
                'has_formula_warnings': len(task_warnings) > 0,
                'formula_errors': task_errors,
                'formula_warnings': task_warnings,
            }
            
            # Добавляем дополнительные поля
            task_data.update(additional_fields)
            
            # Генерируем итоговый HTML код с учетом изображений
            try:
                if task_images:
                    print(f"🔍 HTML: Вызываем render_task_with_images_html с {len(task_images)} изображениями")
                    html_content = render_task_with_images_html(
                        {'text': task_data['text']}, 
                        task_images
                    )
                    print(f"🔍 HTML: render_task_with_images_html вернул: {len(html_content)} символов")
                    task_data['html_content'] = html_content
                else:
                    print("🔍 HTML: Нет изображений, используем обычный текст")
                    task_data['html_content'] = task_data['text']
            except Exception as e:
                print(f"❌ ОШИБКА в HTML render_task_with_images: {e}")
                task_data['html_content'] = task_data['text']  # Fallback
            
            prepared_tasks.append(task_data)
            variant_errors.extend(task_errors)
            variant_warnings.extend(task_warnings)
        
        return {
            'variant': variant,
            'tasks': prepared_tasks,
            'total_tasks': len(prepared_tasks),
            'errors': variant_errors,
            'warnings': variant_warnings,
        }
    
    def generate_with_answers(self, work):
        """Генерирует HTML работу с ответами"""
        self._with_answers = True
        try:
            return self.generate(work)
        finally:
            self._with_answers = False
