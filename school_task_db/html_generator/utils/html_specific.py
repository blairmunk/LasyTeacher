"""HTML специфичные утилиты для обработки формул"""

import re
from typing import Dict, Any
from document_generator.utils.formula_utils import formula_processor as base_processor

class HtmlFormulaProcessor:
    """HTML специфичный процессор формул с поддержкой MathJax"""
    
    def __init__(self):
        self.base_processor = base_processor
    
    def render_for_html_safe(self, text: str) -> Dict[str, Any]:
        """HTML специфичное безопасное преобразование для MathJax"""
        if not text:
            return {'content': text, 'errors': [], 'warnings': []}
        
        # Анализируем формулы в исходном тексте
        processed = self.process_text_safe(text)
        
        if not processed['has_math']:
            # Если формул нет, экранируем HTML символы
            safe_text = self._escape_html(text)
            return {'content': safe_text, 'errors': [], 'warnings': []}
        
        # Обрабатываем текст с формулами
        safe_text = text
        all_errors = []
        all_warnings = []
        
        # Обрабатываем формулы в порядке убывания позиций
        formulas_by_position = sorted(processed['formulas'], key=lambda f: f['position'][0], reverse=True)
        
        for formula in formulas_by_position:
            start, end = formula['position']
            
            if not formula['validation']['is_valid']:
                # Проблемные формулы заменяем на HTML span
                errors = formula['validation']['errors']
                
                if any('опасная команда' in error.lower() for error in errors):
                    safe_replacement = '<span class="blocked-formula" style="color: red; font-weight: bold;">[ЗАБЛОКИРОВАННАЯ КОМАНДА]</span>'
                else:
                    error_count = len(errors)
                    error_list = '; '.join(errors)
                    safe_replacement = f'<span class="formula-error" style="color: orange; font-weight: bold;" title="{self._escape_html(error_list)}">[ОШИБКА: {error_count} проблем]</span>'
                
                all_errors.extend(formula['validation']['errors'])
                all_warnings.extend(formula['validation']['warnings'])
            else:
                # Корректные формулы оставляем для MathJax - НЕ изменяем!
                # MathJax сам обработает $...$ и $$...$$
                safe_replacement = formula['original']
            
            # Заменяем формулу
            safe_text = safe_text[:start] + safe_replacement + safe_text[end:]
        
        # Экранируем HTML символы в тексте, НО НЕ в формулах
        safe_text = self._escape_html_preserve_formulas(safe_text)
        
        return {
            'content': safe_text,
            'errors': all_errors,
            'warnings': all_warnings
        }
    
    def _escape_html(self, text: str) -> str:
        """Экранирует HTML символы"""
        if not text:
            return text
        
        html_escape_table = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        
        result = text
        for char, escaped in html_escape_table.items():
            result = result.replace(char, escaped)
        
        return result
    
    def _escape_html_preserve_formulas(self, text: str) -> str:
        """Экранирует HTML символы, но сохраняет формулы для MathJax"""
        if not text:
            return text
        
        # Временно заменяем формулы на плейсхолдеры
        formula_placeholders = {}
        placeholder_counter = 0
        temp_text = text
        
        def save_formula(match):
            nonlocal placeholder_counter
            placeholder = f"FORMULAPLACEHOLDER{placeholder_counter}FORMULAPLACEHOLDER"
            formula_placeholders[placeholder] = match.group(0)
            placeholder_counter += 1
            return placeholder
        
        # Сохраняем все типы формул
        formula_patterns = [
            r'\$\$[^$]*\$\$',  # $$...$$
            r'\$[^$]+?\$',     # $...$
            # ДОБАВЛЕНО: Сохраняем HTML теги от предыдущей обработки
            r'<span[^>]*class="[^"]*formula[^"]*"[^>]*>.*?</span>',  # HTML span с формулами
        ]
        
        for pattern in formula_patterns:
            temp_text = re.sub(pattern, save_formula, temp_text, flags=re.DOTALL)
        
        # Экранируем HTML символы в тексте без формул
        escaped_text = self._escape_html(temp_text)
        
        # Возвращаем формулы обратно БЕЗ изменений
        for placeholder, original in formula_placeholders.items():
            escaped_text = escaped_text.replace(placeholder, original)
        
        return escaped_text
    
    def __getattr__(self, name):
        """Проксируем все остальные методы к базовому процессору"""
        return getattr(self.base_processor, name)

# Создаем HTML специфичный экземпляр
html_formula_processor = HtmlFormulaProcessor()
