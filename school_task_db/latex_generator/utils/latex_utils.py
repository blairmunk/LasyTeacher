"""LaTeX утилиты для экранирования и форматирования"""

import re

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

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    # Убираем недопустимые символы
    clean = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Убираем лишние пробелы
    clean = re.sub(r'\s+', '_', clean)
    return clean
