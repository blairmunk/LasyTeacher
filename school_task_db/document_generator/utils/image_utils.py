"""Общие утилиты для обработки изображений"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def prepare_images(image, output_dir: Path) -> Optional[Dict]:
    """Универсальная подготовка изображения для генерации документа"""
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

def get_image_dimensions(image_path: Path) -> Dict[str, int]:
    """Получает размеры изображения (универсально)"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return {'width': img.width, 'height': img.height}
    except ImportError:
        logger.warning("PIL не установлен, размеры изображения недоступны")
        return {'width': 0, 'height': 0}
    except Exception as e:
        logger.error(f"Ошибка получения размеров изображения {image_path}: {e}")
        return {'width': 0, 'height': 0}

def optimize_image_for_web(image_path: Path, quality: int = 85) -> Optional[Path]:
    """Оптимизирует изображение для веб-использования"""
    # TODO: ... код оптимизации для HTML/веб использования
    pass


