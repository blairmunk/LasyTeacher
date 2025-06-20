import re
import shutil
from pathlib import Path
from django.conf import settings

def sanitize_latex(text):
    """Экранирует специальные символы LaTeX"""
    if not text:
        return ''
    
    # Словарь замен для LaTeX
    replacements = {
        '\\': r'\textbackslash{}',
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '~': r'\textasciitilde{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    
    # Применяем замены
    result = text
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    
    # Обрабатываем переносы строк
    result = result.replace('\n', '\\\\ ')
    
    return result

def prepare_images(task_image, output_dir):
    """Подготавливает изображение для LaTeX"""
    try:
        # Путь к оригинальному изображению
        original_path = Path(settings.MEDIA_ROOT) / task_image.image.name
        
        if not original_path.exists():
            return None
        
        # Копируем изображение в папку вывода
        image_filename = f"image_{task_image.task.id}_{task_image.id}{original_path.suffix}"
        dest_path = output_dir / image_filename
        shutil.copy2(original_path, dest_path)
        
        # Определяем параметры позиционирования для LaTeX
        latex_position = get_latex_position(task_image.position)
        
        return {
            'filename': image_filename,
            'caption': sanitize_latex(task_image.caption),
            'position': task_image.position,
            'latex_position': latex_position,
            'order': task_image.order,
        }
        
    except Exception as e:
        print(f"⚠️ Ошибка при подготовке изображения {task_image.id}: {e}")
        return None

def get_latex_position(position):
    """Преобразует позицию изображения в LaTeX параметры"""
    positions = {
        'right_40': {'width': '0.4\\textwidth', 'placement': 'wrapfigure', 'align': 'r'},
        'right_20': {'width': '0.2\\textwidth', 'placement': 'wrapfigure', 'align': 'r'},
        'bottom_100': {'width': '\\textwidth', 'placement': 'figure', 'align': 'center'},
        'bottom_70': {'width': '0.7\\textwidth', 'placement': 'figure', 'align': 'center'},
    }
    
    return positions.get(position, positions['bottom_70'])
