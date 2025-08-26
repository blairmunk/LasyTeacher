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
        """Генерирует HTML документ с принудительной UTF-8 кодировкой"""
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
            
            # ИСПРАВЛЕНО: Убеждаемся что контент в UTF-8
            if isinstance(html_content, str):
                html_content = html_content.encode('utf-8').decode('utf-8')
            
            # Генерируем имя файла и сохраняем
            output_filename = sanitize_filename(self.get_output_filename(obj))
            if not output_filename.endswith('.html'):
                output_filename += '.html'
            
            output_path = self.output_dir / output_filename
            
            # ИСПРАВЛЕНО: Явно указываем кодировку при сохранении
            with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(html_content)
            
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
        """ИСПРАВЛЕНО: CSS с улучшенной поддержкой печати"""
        return """
        <style>
        /* ================================
        БАЗОВЫЕ СТИЛИ ДОКУМЕНТА
        ================================ */
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
        
        /* ================================
        БЛОК: ВАРИАНТ
        ================================ */
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
        
        /* ================================
        БЛОК: ЗАДАНИЕ 
        ================================ */
        .task {
            margin-bottom: 25px;
            padding: 15px;
            border-left: 3px solid #007bff;
            background-color: #f8f9fa;
            break-inside: avoid;
        }
        
        .task__number {
            font-weight: bold;
            margin-bottom: 10px;
            color: #007bff;
        }
        
        .task__content {
            margin-bottom: 10px;
        }
        
        .task__answer {
            margin-top: 15px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            font-style: italic;
        }
        
        /* ================================
        БЛОК: ЗАДАНИЕ С ИЗОБРАЖЕНИЕМ
        ================================ */
        .task-with-image {
            margin: 15px 0;
        }
        
        .task-with-image__text {
            margin-bottom: 15px;
        }
        
        .task-with-image__image {
            text-align: center;
        }
        
        .task-with-image__img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .task-with-image__caption {
            margin-top: 8px;
            font-size: 12px;
            color: #666;
            font-style: italic;
        }
        
        /* ================================
        МОДИФИКАТОР: ГОРИЗОНТАЛЬНЫЙ LAYOUT
        ================================ */
        .task-with-image_layout_horizontal {
            display: flex;
            align-items: flex-start;
            gap: 20px;
        }
        
        .task-with-image_layout_horizontal .task-with-image__text {
            flex: 1;
            margin-bottom: 0;
            min-width: 0;
        }
        
        .task-with-image_layout_horizontal .task-with-image__image {
            flex-shrink: 0;
        }
        
        /* ================================
        МОДИФИКАТОРЫ: РАЗМЕРЫ ИЗОБРАЖЕНИЯ
        ================================ */
        .task-with-image_image-size_20 .task-with-image__image {
            width: 20%;
        }
        
        .task-with-image_image-size_40 .task-with-image__image {
            width: 40%;
        }
        
        .task-with-image_image-size_70 .task-with-image__image {
            width: 70%;
            margin: 0 auto;
        }
        
        .task-with-image_image-size_100 .task-with-image__image {
            width: 100%;
        }
        
        /* ================================
        СТИЛИ ДЛЯ ПЕЧАТИ (ПЕРЕРАБОТАНО!)
        ================================ */
        @media print {
            body { 
                margin: 10px;
                font-size: 12pt;
                line-height: 1.4;
            }
            
            .variant-section { 
                page-break-after: always;
            }
            
            .task { 
                break-inside: avoid;
                margin-bottom: 15px;
                padding: 10px;
            }
            
            /* НОВЫЙ ПОДХОД: Float вместо flexbox/table для печати */
            .task-with-image_layout_horizontal {
                display: block !important;
                overflow: hidden;  /* clearfix */
                zoom: 1; /* IE clearfix */
            }
            
            .task-with-image_layout_horizontal .task-with-image__text {
                display: block !important;
                float: left;
                margin-bottom: 0 !important;
                padding-right: 15px;
                box-sizing: border-box;
            }
            
            .task-with-image_layout_horizontal .task-with-image__image {
                display: block !important;
                float: right;
                text-align: center;
                box-sizing: border-box;
            }
            
            /* Четкие размеры для печати */
            .task-with-image_image-size_20 .task-with-image__text {
                width: 75% !important;
            }
            .task-with-image_image-size_20 .task-with-image__image {
                width: 20% !important;
            }
            
            .task-with-image_image-size_40 .task-with-image__text {
                width: 55% !important;
            }
            .task-with-image_image-size_40 .task-with-image__image {
                width: 40% !important;
            }
            
            /* Изображения в печати */
            .task-with-image__img {
                max-width: 100% !important;
                height: auto !important;
                border: 1px solid #999 !important;
                page-break-inside: avoid;
            }
            
            .task-with-image__caption {
                font-size: 10pt !important;
                color: #333 !important;
                margin-top: 5px !important;
            }
            
            /* Очистка float */
            .task-with-image_layout_horizontal:after {
                content: "";
                display: table;
                clear: both;
            }
            
            /* Вертикальные остаются простыми */
            .task-with-image_layout_vertical .task-with-image__image {
                margin: 15px auto !important;
                display: block !important;
            }
            
            /* Скрываем лишнее при печати */
            .document-footer {
                page-break-before: always;
                font-size: 8pt !important;
            }
            
            /* Принудительные цвета для печати */
            * {
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
            }
        }
        
        /* ================================
        RESPONSIVE ДИЗАЙН
        ================================ */
        @media (max-width: 768px) {
            .task-with-image_layout_horizontal {
                flex-direction: column;
            }
            
            .task-with-image_layout_horizontal .task-with-image__text {
                margin-bottom: 15px;
            }
            
            .task-with-image_layout_horizontal .task-with-image__image {
                width: 100% !important;
            }
        }
        
        /* ================================
        СТИЛИ ДЛЯ ФОРМУЛ MATHJAX
        ================================ */
        .MathJax {
            font-size: 1.1em !important;
        }
        
        /* Ошибки формул */
        .formula-error {
            color: orange;
            font-weight: bold;
        }
        
        .blocked-formula {
            color: red;
            font-weight: bold;
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
