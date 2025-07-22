"""Экспорт основных утилит с новыми импортами"""

# НОВЫЕ ИМПОРТЫ из document_generator
from document_generator.utils.file_utils import sanitize_filename
from document_generator.utils.image_utils import prepare_images, render_task_with_images

# СТАРЫЕ ИМПОРТЫ (LaTeX специфичные)
from .latex_utils import sanitize_latex  # Остается в latex_generator
from .compilation import compile_latex_to_pdf, latex_compiler

__all__ = [
    'sanitize_latex',
    'sanitize_filename', 
    'prepare_images',
    'render_task_with_images',
    'compile_latex_to_pdf',
    'latex_compiler',
]
