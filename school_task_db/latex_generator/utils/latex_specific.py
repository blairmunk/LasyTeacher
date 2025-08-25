"""LaTeX специфичные утилиты"""

import re
from typing import Dict, Any
from document_generator.utils.formula_utils import formula_processor as base_processor
from .latex_utils import sanitize_latex

class LaTeXFormulaProcessor:
    """LaTeX специфичный процессор формул"""
    
    def __init__(self):
        self.base_processor = base_processor
    
    def render_for_latex_safe(self, text: str) -> Dict[str, Any]:
        """ИСПРАВЛЕНО: Простая и надежная логика обработки"""
        if not text:
            return {'content': text, 'errors': [], 'warnings': []}
        
        # ШАГ 1: Анализируем и обрабатываем формулы в исходном тексте
        processed = self.process_text_safe(text)
        
        if not processed['has_math']:
            # Если формул нет, просто очищаем и экранируем весь текст
            cleaned_text = self._sanitize_dangerous_latex_completely(text)
            safe_text = sanitize_latex(cleaned_text)
            return {'content': safe_text, 'errors': [], 'warnings': []}
        
        # ШАГ 2: Заменяем формулы в порядке убывания позиций
        safe_text = text
        all_errors = []
        all_warnings = []
        
        formulas_by_position = sorted(processed['formulas'], key=lambda f: f['position'][0], reverse=True)
        
        for formula in formulas_by_position:
            start, end = formula['position']
            
            if not formula['validation']['is_valid']:
                # Проблемные формулы заменяем на текст
                errors = formula['validation']['errors']
                
                if any('опасная команда' in error.lower() for error in errors):
                    safe_replacement = "\\textbf{[ЗАБЛОКИРОВАННАЯ КОМАНДА]}"
                else:
                    error_count = len(errors)
                    safe_replacement = f"\\textbf{{[ОШИБКА: {error_count} проблем]}}"
                
                all_errors.extend(formula['validation']['errors'])
                all_warnings.extend(formula['validation']['warnings'])
            else:
                # Корректные формулы преобразуем в LaTeX формат
                if formula['type'] == 'display':
                    safe_replacement = f"\\[{formula['content']}\\]"
                else:
                    safe_replacement = f"\\({formula['content']}\\)"
            
            # Заменяем формулу
            safe_text = safe_text[:start] + safe_replacement + safe_text[end:]
        
        # ШАГ 3: Очищаем от опасных команд
        safe_text = self._sanitize_dangerous_latex_completely(safe_text)
        
        # ШАГ 4: Экранируем LaTeX символы, НО не трогаем \(...\) и \[...\]
        safe_text = self._smart_sanitize_latex(safe_text)
        
        return {
            'content': safe_text,
            'errors': all_errors,
            'warnings': all_warnings
        }

    def _smart_sanitize_latex(self, text: str) -> str:
        """ИСПРАВЛЕНО: Умное экранирование с плейсхолдерами БЕЗ подчеркиваний"""
        if not text:
            return text
        
        # Временно заменяем LaTeX математические окружения
        math_placeholders = {}
        placeholder_counter = 0
        temp_text = text
        
        def save_latex_math(match):
            nonlocal placeholder_counter
            # ИСПРАВЛЕНО: Плейсхолдер БЕЗ подчеркиваний и спецсимволов
            placeholder = f"LATEXMATHBLOCK{placeholder_counter}LATEXMATHBLOCK"
            math_placeholders[placeholder] = match.group(0)
            placeholder_counter += 1
            return placeholder
        
        # Ищем \(...\) окружения (inline math)
        temp_text = re.sub(r'\\\([^)]*\\\)', save_latex_math, temp_text)
        # Ищем \[...\] окружения (display math)  
        temp_text = re.sub(r'\\\[[^\]]*\\\]', save_latex_math, temp_text)
        
        # Экранируем специальные символы в оставшемся тексте
        sanitized_text = sanitize_latex(temp_text)
        
        # ИСПРАВЛЕНО: Возвращаем математические окружения обратно
        # Теперь плейсхолдеры не изменились после sanitize_latex
        for placeholder, original in math_placeholders.items():
            sanitized_text = sanitized_text.replace(placeholder, original)
        
        return sanitized_text
    
    def __getattr__(self, name):
        """ДОБАВЛЕНО: Проксируем все остальные методы к базовому процессору"""
        return getattr(self.base_processor, name)

# Создаем LaTeX специфичный экземпляр
latex_formula_processor = LaTeXFormulaProcessor()
