"""Утилиты для обработки изображений в LaTeX"""

import shutil
from pathlib import Path
from django.conf import settings
from .latex_utils import sanitize_latex

def prepare_images(task_image, output_dir):
    """Подготавливает изображение для LaTeX"""
    try:
        # Путь к оригинальному изображению
        if hasattr(task_image.image, 'path'):
            original_path = Path(task_image.image.path)
        else:
            # Если путь относительный
            original_path = Path(settings.MEDIA_ROOT) / task_image.image.name
        
        if not original_path.exists():
            print(f"⚠️ Изображение не найдено: {original_path}")
            return None
        
        # Копируем изображение в папку вывода
        image_filename = f"image_{task_image.task.id}_{task_image.id}{original_path.suffix}"
        dest_path = output_dir / image_filename
        shutil.copy2(original_path, dest_path)
        
        return {
            'filename': image_filename,
            'caption': sanitize_latex(task_image.caption or ''),
            'position': task_image.position,
            'order': task_image.order,
        }
        
    except Exception as e:
        print(f"⚠️ Ошибка при подготовке изображения {task_image.id}: {e}")
        return None
