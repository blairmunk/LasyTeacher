"""Генератор LaTeX для работ с поддержкой математических формул"""

from typing import Dict, Any
from latex_generator.utils import sanitize_latex, prepare_images, render_task_with_images
from latex_generator.utils.formula_utils import formula_processor
from .base import BaseLatexGenerator
import logging

logger = logging.getLogger(__name__)

class WorkLatexGenerator(BaseLatexGenerator):
    """Генератор LaTeX документов для работ с математическими формулами"""
    
    def get_template_name(self) -> str:
        return 'latex/work/all_variants.tex'
    
    def get_output_filename(self, work) -> str:
        return f"{work.name}_all_variants.tex"
    
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
        work_name_processed = formula_processor.render_for_latex_safe(work.name)
        document_errors.extend(work_name_processed['errors'])
        document_warnings.extend(work_name_processed['warnings'])
        
        return {
            'work': work,
            'work_name': work_name_processed['content'],
            'variants': all_variants_data,
            'total_variants': len(all_variants_data),
            'with_answers': getattr(self, '_with_answers', False),
            
            # НОВОЕ: информация об ошибках
            'has_formula_errors': len(document_errors) > 0,
            'has_formula_warnings': len(document_warnings) > 0,
            'formula_errors': document_errors,
            'formula_warnings': document_warnings,
        }
    
    def _prepare_variant_context(self, variant):
        """Подготавливает контекст для одного варианта с обработкой формул"""
        tasks = variant.tasks.all().order_by('id')
        
        prepared_tasks = []
        variant_errors = []
        variant_warnings = []
        
        for i, task in enumerate(tasks, 1):
            # Обрабатываем текст задания
            text_processed = formula_processor.render_for_latex_safe(task.text)
            answer_processed = formula_processor.render_for_latex_safe(task.answer)
            
            # Собираем ошибки и предупреждения
            task_errors = []
            task_warnings = []
            
            task_errors.extend(text_processed['errors'])
            task_errors.extend(answer_processed['errors'])
            task_warnings.extend(text_processed['warnings'])
            task_warnings.extend(answer_processed['warnings'])
            
            # Обрабатываем дополнительные поля если есть
            short_solution_processed = {'content': '', 'errors': [], 'warnings': []}
            full_solution_processed = {'content': '', 'errors': [], 'warnings': []}
            hint_processed = {'content': '', 'errors': [], 'warnings': []}
            
            if task.short_solution:
                short_solution_processed = formula_processor.render_for_latex_safe(task.short_solution)
                task_errors.extend(short_solution_processed['errors'])
                task_warnings.extend(short_solution_processed['warnings'])
            
            if task.full_solution:
                full_solution_processed = formula_processor.render_for_latex_safe(task.full_solution)
                task_errors.extend(full_solution_processed['errors'])
                task_warnings.extend(full_solution_processed['warnings'])
            
            if task.hint:
                hint_processed = formula_processor.render_for_latex_safe(task.hint)
                task_errors.extend(hint_processed['errors'])
                task_warnings.extend(hint_processed['warnings'])
            
            # Подготавливаем изображения
            task_images = []
            for image in task.images.all().order_by('order'):
                image_data = prepare_images(image, self.output_dir)
                if image_data:
                    task_images.append(image_data)
            
            # Базовые данные задания с обработанными формулами
            task_data = {
                'number': i,
                'task': task,
                'text': text_processed['content'],  # Уже обработано для LaTeX
                'answer': answer_processed['content'],
                'short_solution': short_solution_processed['content'],
                'full_solution': full_solution_processed['content'],
                'hint': hint_processed['content'],
                'images': task_images,
                
                # Информация об ошибках формул
                'has_formula_errors': len(task_errors) > 0,
                'has_formula_warnings': len(task_warnings) > 0,
                'formula_errors': task_errors,
                'formula_warnings': task_warnings,
            }
            
            # Генерируем итоговый LaTeX код с учетом изображений
            if task_images:
                # Если есть изображения, используем существующую логику minipage
                task_data['latex_content'] = render_task_with_images(
                    {'text': task_data['text']}, 
                    task_images
                )
            else:
                # Если нет изображений, просто используем обработанный текст
                task_data['latex_content'] = task_data['text']
            
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
    
    def generate(self, work, output_format='pdf'):
        """Переопределенная генерация с логированием ошибок формул"""
        try:
            # Вызываем базовую генерацию
            files = super().generate(work, output_format)
            
            # Проверяем наличие ошибок формул в контексте
            context = self.prepare_context(work)
            
            if context.get('has_formula_errors'):
                logger.warning(f"Работа {work.name} содержит ошибки в формулах: {context['formula_errors']}")
            
            if context.get('has_formula_warnings'):
                logger.info(f"Работа {work.name} содержит предупреждения в формулах: {context['formula_warnings']}")
            
            return files
            
        except Exception as e:
            logger.error(f"Ошибка генерации LaTeX для работы {work.name}: {e}")
            raise
    
    def generate_with_answers(self, work, output_format='pdf'):
        """Генерирует работу с ответами"""
        self._with_answers = True
        try:
            return self.generate(work, output_format)
        finally:
            self._with_answers = False
