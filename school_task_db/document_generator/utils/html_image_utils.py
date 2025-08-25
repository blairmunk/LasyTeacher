"""HTML специфичные утилиты для обработки изображений"""

import base64
from pathlib import Path
from typing import Dict, List
from .image_utils import prepare_images

def prepare_images_for_html(task, output_dir: Path) -> List[Dict]:
    """Подготавливает изображения для HTML с base64 кодировкой и CSS классами"""
    html_images = []
    
    for image in task.images.all().order_by('order'):
        # Используем общую функцию подготовки
        image_data = prepare_images(image, output_dir)
        
        if image_data:
            # Дополнительно создаем base64 версию для HTML
            image_path = Path(image_data['path'])
            if image_path.exists():
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
                    mime_type = get_image_mime_type(image_path.suffix)
                
                html_images.append({
                    **image_data,  # Базовые данные
                    'base64': base64_data,
                    'mime_type': mime_type,
                    'html_class': get_html_css_class(image.position),
                    'data_uri': f"data:{mime_type};base64,{base64_data}",
                })
    
    return html_images

def get_image_mime_type(extension: str) -> str:
    """Определяет MIME тип для HTML"""
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', 
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
    }
    return mime_types.get(extension.lower(), 'image/jpeg')

def get_html_css_class(position: str) -> str:
    """Возвращает CSS класс для HTML позиции изображения"""
    css_classes = {
        'right_40': 'image-right image-40',
        'right_20': 'image-right image-20',
        'bottom_100': 'image-bottom image-100',
        'bottom_70': 'image-bottom image-70',
    }
    return css_classes.get(position, 'image-bottom image-70')

def render_task_with_images_html(task_data, images):
    """Генерирует HTML код для задания с изображениями"""
    if not images:
        return task_data['text']
    
    # HTML специфичная логика
    first_image = images[0]
    position = first_image['position']
    
    if position.startswith('right_'):
        return generate_side_by_side_html(task_data, first_image)
    else:
        return generate_vertical_html(task_data, first_image)

def generate_side_by_side_html(task_data, image):
    """Генерирует HTML код для бок-о-бок компоновки"""
    width_class = f"image-{image['position'].split('_')[1]}"  # right_40 -> image-40
    
    return f"""
    <div class="task-with-image-horizontal">
        <div class="task-text {width_class}">
            {task_data['text']}
        </div>
        <div class="task-image image-right">
            <img src="{image['data_uri']}" alt="{image['caption']}" class="{image['html_class']}">
            {f'<div class="image-caption">{image["caption"]}</div>' if image['caption'] else ''}
        </div>
    </div>
    """

def generate_vertical_html(task_data, image):
    """Генерирует HTML код для вертикальной компоновки"""
    return f"""
    <div class="task-with-image-vertical">
        <div class="task-text">
            {task_data['text']}
        </div>
        <div class="task-image image-bottom">
            <img src="{image['data_uri']}" alt="{image['caption']}" class="{image['html_class']}">
            {f'<div class="image-caption">{image["caption"]}</div>' if image['caption'] else ''}
        </div>
    </div>
    """
