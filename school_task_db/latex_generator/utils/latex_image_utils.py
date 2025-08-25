"""LaTeX специфичные утилиты для обработки изображений"""

from typing import Dict, List
from document_generator.utils.image_utils import prepare_images
from .latex_utils import sanitize_latex

def prepare_images_for_latex(task, output_dir) -> List[Dict]:
    """Подготавливает изображения для LaTeX с minipage конфигурацией"""
    print(f"🔍 prepare_images_for_latex: обрабатываем задание {task.id}")
    
    latex_images = []
    
    for image in task.images.all().order_by('order'):
        print(f"🔍 Обрабатываем изображение {image.id}, позиция: {image.position}")
        
        # Используем общую функцию подготовки
        image_data = prepare_images(image, output_dir)
        
        if image_data:
            print(f"🔍 prepare_images вернул данные: {list(image_data.keys())}")
            
            # ДОБАВЛЯЕМ LaTeX специфичную конфигурацию
            minipage_config = get_minipage_config(image_data['position'])
            print(f"🔍 minipage_config: {minipage_config}")
            
            latex_images.append({
                **image_data,  # Базовые данные из общей функции
                'minipage_config': minipage_config,  # LaTeX специфичные настройки
            })
            print(f"🔍 Добавлено изображение в latex_images, итого: {len(latex_images)}")
        else:
            print(f"❌ prepare_images вернул None для изображения {image.id}")
    
    print(f"🔍 prepare_images_for_latex возвращает {len(latex_images)} изображений")
    return latex_images

def get_minipage_config(position):
    """LaTeX специфичная конфигурация minipage для разных позиций изображений"""
    
    configs = {
        'right_40': {
            'layout': 'side_by_side',
            'text_width': '0.55\\textwidth',
            'image_width': '0.4\\textwidth',
            'text_align': '[t]',      
            'image_align': '[t]',
            'spacing': '\\hfill',
            'image_position': 'right',
            'vertical_adjust': '\\vspace*{-3em}',
        },
        'right_20': {
            'layout': 'side_by_side',
            'text_width': '0.75\\textwidth',
            'image_width': '0.2\\textwidth',
            'text_align': '[t]',      
            'image_align': '[t]',
            'spacing': '\\hfill',
            'image_position': 'right',
            'vertical_adjust': '\\vspace*{-3em}',
        },
        'bottom_100': {
            'layout': 'vertical',
            'text_width': '\\textwidth',
            'image_width': '\\textwidth',
            'image_align': '[c]',
            'spacing': '\\vspace{0.5cm}',
            'image_position': 'bottom',
            'center_image': True,
        },
        'bottom_70': {
            'layout': 'vertical',
            'text_width': '\\textwidth',
            'image_width': '0.7\\textwidth',
            'image_align': '[c]',
            'spacing': '\\vspace{0.5cm}',
            'image_position': 'bottom',
            'center_image': True,
        },
    }
    
    return configs.get(position, configs['bottom_70'])

def render_task_with_images(task_data, images):
    """Генерирует LaTeX код для задания с изображениями используя minipage"""
    
    print(f"🔍 render_task_with_images: получено {len(images)} изображений")
    
    if not images:
        print("🔍 Нет изображений, возвращаем обычный текст")
        return task_data['text']
    
    # Проверяем первое изображение
    first_image = images[0]
    print(f"🔍 Первое изображение: {list(first_image.keys())}")
    
    if 'minipage_config' not in first_image:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: minipage_config отсутствует!")
        return task_data['text']
    
    config = first_image['minipage_config']
    print(f"🔍 minipage_config: layout = {config['layout']}")
    
    if config['layout'] == 'side_by_side':
        print("🔍 Генерируем side_by_side minipage")
        result = generate_side_by_side_minipage(task_data, first_image, config)
    else:
        print("🔍 Генерируем vertical minipage")
        result = generate_vertical_minipage(task_data, first_image, config)
    
    print(f"🔍 Сгенерированный LaTeX код ({len(result)} символов):")
    print("=" * 50)
    print(result)
    print("=" * 50)
    
    return result

def generate_side_by_side_minipage(task_data, image, config):
    """Генерирует горизонтальную компоновку с minipage"""
    
    text_align = config.get('text_align', '[t]')  
    vertical_adjust = config.get('vertical_adjust', '')
    
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
        # ИСПРАВЛЕНО: Экранируем подпись изображения
        safe_caption = sanitize_latex(image['caption'])
        latex_code += f"""
\\\\[0.2cm]
\\small\\textit{{{safe_caption}}}"""
    
    latex_code += """
\\end{minipage}
"""
    
    return latex_code

def generate_vertical_minipage(task_data, image, config):
    """ИСПРАВЛЕНО: Генерирует вертикальную компоновку с minipage"""
    
    latex_code = f"""
% Вертикальная компоновка с minipage - текст сверху, изображение снизу
\\noindent
\\begin{{minipage}}{{{config['text_width']}}}
{task_data['text']}
\\end{{minipage}}

{config['spacing']}

"""
    
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
        # ИСПРАВЛЕНО: ДОБАВЛЕНО экранирование подписи изображения!
        safe_caption = sanitize_latex(image['caption'])
        latex_code += f"""
\\\\[0.2cm]
\\small\\textit{{{safe_caption}}}"""
    
    latex_code += """
\\end{minipage}"""
    
    if config.get('center_image', False):
        latex_code += """
\\end{center}"""
    
    return latex_code