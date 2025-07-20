"""Генератор LaTeX для работ"""

from typing import Dict, Any
from latex_generator.utils import sanitize_latex, prepare_images, render_task_with_images
from .base import BaseLatexGenerator

class WorkLatexGenerator(BaseLatexGenerator):
    """Генератор LaTeX документов для работ"""
    
    def get_template_name(self) -> str:
        return 'latex/work/all_variants.tex'
    
    def get_output_filename(self, work) -> str:
        return f"{work.name}_all_variants.tex"
    
    def prepare_context(self, work) -> Dict[str, Any]:
        """Подготавливает контекст для работы"""
        
        # ИСПРАВЛЕНО: variants -> variant_set
        variants = work.variant_set.all().order_by('number')
        
        # Подготавливаем данные для каждого варианта
        all_variants_data = []
        for variant in variants:
            variant_data = self._prepare_variant_context(variant)
            all_variants_data.append(variant_data)
        
        return {
            'work': work,
            'work_name': sanitize_latex(work.name),
            'variants': all_variants_data,
            'total_variants': len(all_variants_data),
            'with_answers': getattr(self, '_with_answers', False),
        }
    
    def _prepare_variant_context(self, variant):
        """Подготавливает контекст для одного варианта"""
        tasks = variant.tasks.all().order_by('id')  # Детерминированный порядок
        
        # Подготавливаем задания с изображениями
        prepared_tasks = []
        for i, task in enumerate(tasks, 1):
            # Подготавливаем изображения
            task_images = []
            for image in task.images.all().order_by('order'):
                image_data = prepare_images(image, self.output_dir)
                if image_data:
                    task_images.append(image_data)
            
            # Базовые данные задания
            task_data = {
                'number': i,
                'task': task,
                'text': sanitize_latex(task.text),
                'answer': sanitize_latex(task.answer),
                'images': task_images,
            }
            
            # НОВОЕ: Генерируем итоговый LaTeX код с учетом изображений
            task_data['latex_content'] = render_task_with_images(task_data, task_images)
            
            prepared_tasks.append(task_data)
        
        return {
            'variant': variant,
            'tasks': prepared_tasks,
            'total_tasks': len(prepared_tasks),
        }
    
    def generate_with_answers(self, work, output_format='pdf'):
        """Генерирует работу с ответами"""
        self._with_answers = True
        try:
            return self.generate(work, output_format)
        finally:
            self._with_answers = False
