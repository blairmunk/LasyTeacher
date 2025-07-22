"""Общие утилиты для работы с файлами"""

import re
import os
import tempfile
from pathlib import Path
from typing import Union

def sanitize_filename(filename: str) -> str:
    """
    ПЕРЕМЕЩЕНО из latex_generator: Очищает имя файла от недопустимых символов
    """
    if not filename:
        return "untitled"
    
    # Заменяем недопустимые символы
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Заменяем множественные пробелы и подчеркивания
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    
    # Удаляем ведущие и замыкающие подчеркивания
    sanitized = sanitized.strip('_')
    
    # Ограничиваем длину
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    # Убеждаемся что имя не пустое
    if not sanitized:
        sanitized = "untitled"
    
    return sanitized

# TODO: ДОПОЛНИТЕЛЬНЫЕ ОБЩИЕ ФУНКЦИИ...