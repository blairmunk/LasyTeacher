"""LaTeX специфичные утилиты"""

import re
from typing import Dict, Any
from document_generator.utils.formula_utils import formula_processor as base_processor

class LaTeXFormulaProcessor:
    """LaTeX специфичный процессор формул"""
    
    def __init__(self):
        self.base_processor = base_processor
    
    def render_for_latex_safe(self, text: str) -> Dict[str, Any]:
        """LaTeX специфичное безопасное преобразование"""
        if not text:
            return {'content': text, 'errors': [], 'warnings': []}
        
        # ИЗМЕНЕНА ЛОГИКА: Сначала находим формулы в ИСХОДНОМ тексте
        processed = self.process_text_safe(text)
        
        if not processed['has_math']:
            # Если формул нет, просто очищаем от опасных команд вне формул
            cleaned_text = self._sanitize_dangerous_latex_completely(text)
            return {'content': cleaned_text, 'errors': [], 'warnings': []}
        
        # Обрабатываем текст с формулами
        safe_text = text
        all_errors = []
        all_warnings = []
        
        # Обрабатываем формулы в порядке убывания позиций (справа налево)
        # чтобы позиции не сбивались при замене
        formulas_by_position = sorted(processed['formulas'], key=lambda f: f['position'][0], reverse=True)
        
        for formula in formulas_by_position:
            if not formula['validation']['is_valid']:
                # ИСПРАВЛЕНО: Заменяем ВСЮ формулу (включая $ или $$) на безопасный текст
                errors = formula['validation']['errors']
                
                if any('опасная команда' in error.lower() for error in errors):
                    # Для опасных команд - простой текст БЕЗ математических окружений
                    safe_replacement = "\\textbf{[ЗАБЛОКИРОВАННАЯ КОМАНДА]}"
                else:
                    # Для других ошибок
                    error_count = len(errors)
                    safe_replacement = f"\\textbf{{[ОШИБКА: {error_count} проблем]}}"
                
                # Заменяем ВСЮ формулу включая $ или $$
                safe_text = safe_text[:formula['position'][0]] + safe_replacement + safe_text[formula['position'][1]:]
                
                all_errors.extend(formula['validation']['errors'])
                all_warnings.extend(formula['validation']['warnings'])
                
            else:
                # Для корректных формул - преобразуем в LaTeX формат
                if formula['type'] == 'display':
                    latex_formula = f"\\[{formula['content']}\\]"
                else:
                    latex_formula = f"\\({formula['content']}\\)"
                
                # Заменяем формулу на LaTeX версию
                safe_text = safe_text[:formula['position'][0]] + latex_formula + safe_text[formula['position'][1]:]
        
        # Очищаем от опасных команд ВНЕ формул (которые остались)
        safe_text = self._sanitize_dangerous_latex_completely(safe_text)
        
        return {
            'content': safe_text,
            'errors': all_errors,
            'warnings': all_warnings
        }
    
    def __getattr__(self, name):
        """Проксируем все остальные методы к базовому процессору"""
        return getattr(self.base_processor, name)

# Создаем LaTeX специфичный экземпляр
latex_formula_processor = LaTeXFormulaProcessor()
