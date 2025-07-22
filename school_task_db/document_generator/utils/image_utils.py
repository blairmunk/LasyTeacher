"""Общие утилиты для обработки изображений"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


def prepare_images(image, output_dir: Path) -> Optional[Dict]:
    """
    ПЕРЕМЕЩЕНО из latex_generator: Подготавливает изображение для генерации документа
    """
    try:
        # Получаем путь к изображению
        if hasattr(image.image, 'path') and Path(image.image.path).exists():
            image_path = Path(image.image.path)
        elif hasattr(settings, 'MEDIA_ROOT'):
            image_path = Path(settings.MEDIA_ROOT) / image.image.name
            if not image_path.exists():
                logger.warning(f"Изображение не найдено: {image_path}")
                return None
        else:
            logger.warning(f"Не удается определить путь к изображению: {image}")
            return None
        
        # Генерируем уникальное имя файла
        image_filename = f"image_{image.task.id}_{image.id}{image_path.suffix}"
        dest_path = output_dir / image_filename
        
        # Копируем изображение
        shutil.copy2(image_path, dest_path)
        
        logger.debug(f"Изображение скопировано: {image_path} -> {dest_path}")
        
        return {
            'filename': image_filename,
            'path': str(dest_path),
            'caption': image.caption or '',
            'position': image.position,
            'order': image.order,
            'original_path': str(image_path),
        }
        
    except Exception as e:
        logger.error(f"Ошибка подготовки изображения {image.id}: {e}")
        return None

def get_minipage_config(position):
    """Конфигурация minipage для разных позиций изображений"""
    
    configs = {
        'right_40': {
            'layout': 'side_by_side',
            'text_width': '0.55\\textwidth',
            'image_width': '0.4\\textwidth',
            'text_align': '[t]',      
            'image_align': '[t]',
            'spacing': '\\hfill',
            'image_position': 'right',
            'vertical_adjust': '\\vspace*{-3em}',  # ИСПРАВЛЕНИЕ 1: подтягиваем изображение вверх
        },
        'right_20': {
            'layout': 'side_by_side',
            'text_width': '0.75\\textwidth',
            'image_width': '0.2\\textwidth',
            'text_align': '[t]',      
            'image_align': '[t]',
            'spacing': '\\hfill',
            'image_position': 'right',
            'vertical_adjust': '\\vspace*{-3em}',  # ИСПРАВЛЕНИЕ 1: подтягиваем изображение вверх
        },
        'bottom_100': {
            'layout': 'vertical',
            'text_width': '\\textwidth',
            'image_width': '\\textwidth',
            'image_align': '[c]',
            'spacing': '\\vspace{0.5cm}',
            'image_position': 'bottom',
            'center_image': True,     # ИСПРАВЛЕНИЕ 2: центрирование
        },
        'bottom_70': {
            'layout': 'vertical',
            'text_width': '\\textwidth',
            'image_width': '0.7\\textwidth',
            'image_align': '[c]',
            'spacing': '\\vspace{0.5cm}',
            'image_position': 'bottom',
            'center_image': True,     # ИСПРАВЛЕНИЕ 2: центрирование
        },
    }
    
    return configs.get(position, configs['bottom_70'])  # По умолчанию bottom_70

def render_task_with_images(task_data, images):
    """Генерирует LaTeX код для задания с изображениями используя minipage"""
    
    if not images:
        # Без изображений - просто текст
        return task_data['text']
    
    # Группируем изображения по позиции
    images_by_position = {}
    for image in images:
        pos = image['position']
        if pos not in images_by_position:
            images_by_position[pos] = []
        images_by_position[pos].append(image)
    
    # Пока обрабатываем только первое изображение
    # TODO: в следующих коммитах добавить поддержку нескольких изображений
    first_image = images[0]
    config = first_image['minipage_config']
    
    if config['layout'] == 'side_by_side':
        # Горизонтальная компоновка
        return generate_side_by_side_minipage(task_data, first_image, config)
    else:
        # Вертикальная компоновка
        return generate_vertical_minipage(task_data, first_image, config)

def generate_side_by_side_minipage(task_data, image, config):
    """Генерирует горизонтальную компоновку с minipage"""
    
    # ИСПРАВЛЕНИЕ 1: Добавляем выравнивание по верху для ОБЕИХ minipage
    text_align = config.get('text_align', '[t]')  
    vertical_adjust = config.get('vertical_adjust', '')  # Вертикальная коррекция
    
    latex_code = f"""
% Горизонтальная компоновка с minipage - текст слева, изображение справа
% ИСПРАВЛЕНО: оба блока выровнены по верху + вертикальная коррекция
\\noindent
\\begin{{minipage}}{text_align}{{{config['text_width']}}}
{task_data['text']}
\\end{{minipage}}
{config['spacing']}
\\begin{{minipage}}{config['image_align']}{{{config['image_width']}}}
{vertical_adjust}
\\centering
\\includegraphics[width=\\textwidth]{{{image['filename']}}}"""
    
    if image['caption']:
        latex_code += f"""
\\\\[0.2cm]
\\small\\textit{{{image['caption']}}}"""
    
    latex_code += """
\\end{minipage}
"""
    
    return latex_code

def generate_vertical_minipage(task_data, image, config):
    """Генерирует вертикальную компоновку с minipage"""
    
    latex_code = f"""
% Вертикальная компоновка с minipage - текст сверху, изображение снизу
\\noindent
\\begin{{minipage}}{{{config['text_width']}}}
{task_data['text']}
\\end{{minipage}}

{config['spacing']}

"""
    
    # ИСПРАВЛЕНИЕ 2: Добавляем центрирование для изображений с center_image=True
    if config.get('center_image', False):
        latex_code += """
% ИСПРАВЛЕНО: центрирование изображения по горизонтали
\\begin{center}
"""
    
    latex_code += f"""
\\begin{{minipage}}{config['image_align']}{{{config['image_width']}}}
\\centering
\\includegraphics[width=\\textwidth]{{{image['filename']}}}"""
    
    if image['caption']:
        latex_code += f"""
\\\\[0.2cm]
\\small\\textit{{{image['caption']}}}"""
    
    latex_code += """
\\end{minipage}"""
    
    # Закрываем центрирование если оно было добавлено
    if config.get('center_image', False):
        latex_code += """
\\end{center}"""
    
    return latex_code
