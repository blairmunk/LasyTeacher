"""Базовый генератор LaTeX документов"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from django.template.loader import render_to_string
from latex_generator.utils import sanitize_filename, compile_latex_to_pdf

class BaseLatexGenerator(ABC):
    """Абстрактный базовый класс для генераторов LaTeX"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def get_template_name(self) -> str:
        """Возвращает имя шаблона для генерации"""
        pass
    
    @abstractmethod
    def prepare_context(self, source_object: Any) -> Dict[str, Any]:
        """Подготавливает контекст для рендеринга шаблона"""
        pass
    
    @abstractmethod
    def get_output_filename(self, source_object: Any) -> str:
        """Возвращает имя файла для сохранения"""
        pass
    
    def generate(self, source_object: Any, output_format: str = 'pdf') -> List[str]:
        """
        Генерирует LaTeX документ
        
        Args:
            source_object: Объект для генерации (Work, Report, etc.)
            output_format: 'latex' или 'pdf'
            
        Returns:
            Список путей к созданным файлам
        """
        # Подготавливаем контекст
        context = self.prepare_context(source_object)
        
        # Рендерим шаблон
        template_name = self.get_template_name()
        latex_content = render_to_string(template_name, context)
        
        # Сохраняем LaTeX файл
        filename = self.get_output_filename(source_object)
        latex_filename = sanitize_filename(filename)
        latex_file = self.output_dir / latex_filename
        
        with open(latex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        files = [str(latex_file)]
        
        # Компилируем в PDF если нужно
        if output_format == 'pdf':
            pdf_file = compile_latex_to_pdf(latex_file, self.output_dir)
            if pdf_file:
                files.append(str(pdf_file))
        
        return files
