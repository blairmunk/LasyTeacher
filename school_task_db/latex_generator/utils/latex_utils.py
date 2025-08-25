"""LaTeX утилиты для экранирования и форматирования"""

import re

def sanitize_latex(text):
    """ИСПРАВЛЕНО: Экранирует специальные символы LaTeX в правильном порядке"""
    if not text:
        return ''
    
    result = text
    
    # ВАЖНО: Сначала экранируем обратный слеш, потом остальные символы
    # Иначе будет двойное экранирование
    result = result.replace('\\', r'\textbackslash{}')
    
    # Остальные символы (БЕЗ обратного слеша)
    other_replacements = {
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',  # КЛЮЧЕВОЙ символ - подчеркивание
        '~': r'\textasciitilde{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    
    # Применяем остальные замены
    for char, replacement in other_replacements.items():
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
