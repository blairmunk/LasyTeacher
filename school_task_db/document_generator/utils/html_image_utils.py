"""HTML специфичные утилиты для обработки изображений (BEM версия)"""

import base64
from pathlib import Path
from typing import Dict, List
from .image_utils import prepare_images

def prepare_images_for_html(task, output_dir: Path) -> List[Dict]:
    """Подготавливает изображения для HTML с base64 кодировкой и BEM классами"""
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
                
                # Парсим позицию для BEM классов
                bem_classes = get_bem_classes_for_position(image.position)
                
                html_images.append({
                    **image_data,  # Базовые данные
                    'base64': base64_data,
                    'mime_type': mime_type,
                    'data_uri': f"data:{mime_type};base64,{base64_data}",
                    'bem_classes': bem_classes,  # BEM классы вместо html_class
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

def get_bem_classes_for_position(position: str) -> Dict[str, str]:
    """НОВОЕ: Возвращает BEM классы для позиции изображения"""
    
    # Парсим позицию: 'right_40' -> position='right', size='40'  
    parts = position.split('_')
    if len(parts) == 2:
        pos, size = parts
    else:
        pos, size = 'bottom', '70'  # default
    
    # Определяем layout
    layout = 'horizontal' if pos in ['right', 'left'] else 'vertical'
    image_position = pos
    image_size = size
    
    return {
        'container': f'task-with-image task-with-image_layout_{layout} task-with-image_image-position_{image_position} task-with-image_image-size_{image_size}',
        'text': 'task-with-image__text',
        'image': 'task-with-image__image',
        'caption': 'task-with-image__caption',
    }

def render_task_with_images_html(task_data, images):
    """Генерирует HTML код для задания с изображениями (BEM версия)"""
    if not images:
        return task_data['text']
    
    # Берем первое изображение
    first_image = images[0]
    bem_classes = first_image['bem_classes']
    
    return f"""
    <div class="{bem_classes['container']}">
        <div class="{bem_classes['text']}">
            {task_data['text']}
        </div>
        <div class="{bem_classes['image']}">
            <img src="{first_image['data_uri']}" alt="{first_image['caption']}" class="task-with-image__img">
            {f'<div class="{bem_classes["caption"]}">{first_image["caption"]}</div>' if first_image['caption'] else ''}
        </div>
    </div>
    """

# УДАЛЕНЫ: generate_side_by_side_html и generate_vertical_html - заменены на единую функцию
