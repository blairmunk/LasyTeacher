"""Утилиты для обработки изображений в LaTeX с minipage"""

import shutil
from pathlib import Path
from django.conf import settings
from .latex_utils import sanitize_latex

def prepare_images(task_image, output_dir):
    """Подготавливает изображение для LaTeX с minipage"""
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
        
        # Получаем конфигурацию minipage
        minipage_config = get_minipage_config(task_image.position)
        
        return {
            'filename': image_filename,
            'caption': sanitize_latex(task_image.caption or ''),
            'position': task_image.position,
            'minipage_config': minipage_config,
            'order': task_image.order,
        }
        
    except Exception as e:
        print(f"⚠️ Ошибка при подготовке изображения {task_image.id}: {e}")
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
