"""Утилиты для PDF генерации"""

from pathlib import Path
from typing import List, Tuple

def get_output_pdf_path(html_file_path: Path, output_dir: str = None) -> Path:
    """ИСПРАВЛЕНО: Генерирует абсолютный путь к выходному PDF файлу"""
    # ИСПРАВЛЕНО: Преобразуем входной путь в абсолютный
    html_file_path = Path(html_file_path)
    if not html_file_path.is_absolute():
        html_file_path = html_file_path.resolve()
    
    if output_dir:
        output_directory = Path(output_dir)
    else:
        from django.conf import settings
        pdf_settings = getattr(settings, 'PDF_GENERATOR_SETTINGS', {})
        output_directory = Path(pdf_settings.get('OUTPUT_DIR', 'pdf_output'))
    
    # ИСПРАВЛЕНО: Преобразуем выходную директорию в абсолютную
    if not output_directory.is_absolute():
        output_directory = output_directory.resolve()
        
    output_directory.mkdir(parents=True, exist_ok=True)
    
    # Заменяем .html на .pdf, сохраняем имя файла
    pdf_filename = html_file_path.stem + '.pdf'
    return output_directory / pdf_filename

def validate_html_file(html_file_path: Path) -> bool:
    """ИСПРАВЛЕНО: Проверяет HTML файл с абсолютным путем"""
    html_file_path = Path(html_file_path)
    
    # ИСПРАВЛЕНО: Преобразуем в абсолютный путь для проверки
    if not html_file_path.is_absolute():
        html_file_path = html_file_path.resolve()
        
    if not html_file_path.exists():
        return False
    
    try:
        content = html_file_path.read_text(encoding='utf-8')
        # Проверяем основные HTML теги
        required_tags = ['<html', '<head', '<body']
        return all(tag in content.lower() for tag in required_tags)
    except Exception:
        return False

def batch_html_to_pdf_paths(html_files: List[Path], output_dir: str = None) -> List[Tuple[Path, Path]]:
    """Создает пары (HTML_файл, PDF_файл) для batch обработки"""
    pairs = []
    
    for html_file in html_files:
        if validate_html_file(html_file):
            pdf_file = get_output_pdf_path(html_file, output_dir)
            pairs.append((html_file, pdf_file))
        else:
            import logging
            logging.warning(f"Пропускаем некорректный HTML файл: {html_file}")
    
    return pairs

__all__ = [
    'get_output_pdf_path',
    'validate_html_file', 
    'batch_html_to_pdf_paths',
]
