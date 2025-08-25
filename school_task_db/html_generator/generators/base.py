"""Базовый класс для HTML генераторов"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
from django.template.loader import render_to_string
from document_generator.utils.file_utils import sanitize_filename

logger = logging.getLogger(__name__)

class BaseHtmlGenerator(ABC):
    """Базовый класс для генерации HTML документов"""
    
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path('html_output')
        
        # Создаем выходную директорию если её нет
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def get_template_name(self) -> str:
        """Возвращает имя шаблона для генерации"""
        pass
    
    @abstractmethod
    def get_output_filename(self, obj) -> str:
        """Возвращает имя выходного файла"""
        pass
    
    @abstractmethod
    def prepare_context(self, obj) -> Dict[str, Any]:
        """Подготавливает контекст для шаблона"""
        pass
    
    def generate(self, obj, **kwargs) -> List[str]:
        """Генерирует HTML документ"""
        try:
            logger.info(f"Начало генерации HTML для {obj}")
            
            # Подготавливаем контекст
            context = self.prepare_context(obj)
            
            # Добавляем общие переменные контекста
            context.update({
                'generator_type': 'html',
                'timestamp': self._get_timestamp(),
                'css_styles': self._get_css_styles(),
                'js_scripts': self._get_js_scripts(),
            })
            
            # Рендерим шаблон
            template_name = self.get_template_name()
            html_content = render_to_string(template_name, context)
            
            # Генерируем имя файла и сохраняем
            output_filename = sanitize_filename(self.get_output_filename(obj))
            if not output_filename.endswith('.html'):
                output_filename += '.html'
            
            output_path = self.output_dir / output_filename
            
            # Сохраняем HTML файл
            output_path.write_text(html_content, encoding='utf-8')
            
            logger.info(f"HTML документ сохранен: {output_path}")
            
            return [str(output_path)]
            
        except Exception as e:
            logger.error(f"Ошибка генерации HTML для {obj}: {e}")
            raise
    
    def _get_timestamp(self) -> str:
        """Возвращает текущий timestamp для документа"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_css_styles(self) -> str:
        """Возвращает CSS стили для документа"""
        return """
        <style>
        /* Базовые стили для HTML документов */
        body {
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.6;
            margin: 40px;
            background-color: #ffffff;
        }
        
        .document-header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
        }
        
        .document-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .variant-section {
            margin-bottom: 40px;
            page-break-after: always;
        }
        
        .variant-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }
        
        .task {
            margin-bottom: 25px;
            padding: 15px;
            border-left: 3px solid #007bff;
            background-color: #f8f9fa;
        }
        
        .task-number {
            font-weight: bold;
            margin-bottom: 10px;
            color: #007bff;
        }
        
        .task-text {
            flex: 1;  /* ИСПРАВЛЕНО: Текст занимает оставшееся место */
            min-width: 0; /* Позволяет тексту сжиматься */
        }
        
        .task-answer {
            margin-top: 15px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            font-style: italic;
        }
        
        /* Стили для изображений */
        .task-with-image-horizontal {
            display: flex;
            align-items: flex-start;
            gap: 20px;
            margin: 15px 0;
        }
        
        .task-with-image-vertical {
            margin: 15px 0;
        }
        
        .task-image {
            flex-shrink: 0; /* ИСПРАВЛЕНО: Изображение не сжимается */
            text-align: center;
        }
        
        .task-image img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .image-caption {
            margin-top: 8px;
            font-size: 12px;
            color: #666;
            font-style: italic;
        }
        
        .image-right {
            flex-shrink: 0;
        }
        
        /* ИСПРАВЛЕНО: Классы ширины применяются к контейнеру изображения */
        .task-image.image-40 { 
            width: 40%; 
            max-width: 40%;
        }
        
        .task-image.image-20 { 
            width: 20%; 
            max-width: 20%;
        }
        
        .task-image.image-70 { 
            width: 70%; 
            max-width: 70%;
        }
        
        .task-image.image-100 { 
            width: 100%; 
            max-width: 100%;
        }

        /* Стили для вертикального отображения остаются */
        .image-bottom {
            display: block;
            margin: 20px auto;
        }

        /* ДОБАВЛЕНО: Responsive поведение */
        @media (max-width: 768px) {
            .task-with-image-horizontal {
                flex-direction: column;
            }
            
            .task-image.image-40,
            .task-image.image-20 {
                width: 100% !important;
                max-width: 100% !important;
            }
        }
        
        /* Стили для печати */
        @media print {
            body { margin: 20px; }
            .variant-section { page-break-after: always; }
            .task { break-inside: avoid; }
        }
        
        /* Стили для формул MathJax */
        .MathJax {
            font-size: 1.1em !important;
        }

        /* ДОПОЛНИТЕЛЬНО: Улучшенные отступы и выравнивание */
        .task-with-image-horizontal .task-text {
            padding-right: 10px; /* Немного отступа от изображения */
        }

        .task-with-image-horizontal .task-image {
            padding-left: 10px;  /* Немного отступа от текста */
        }

        /* Улучшенное вертикальное выравнивание */
        .task-with-image-horizontal {
            align-items: flex-start; /* Выравнивание по верху */
        }

        /* Если нужно выравнивание по центру */
        .task-with-image-horizontal.align-center {
            align-items: center;
        }

        </style>
        """
    
    def _get_js_scripts(self) -> str:
        """Возвращает JavaScript скрипты для документа (MathJax)"""
        return """
        <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                packages: {'[+]': ['ams', 'newcommand', 'configMacros']}
            },
            svg: {
                fontCache: 'global'
            }
        };
        </script>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
        """
