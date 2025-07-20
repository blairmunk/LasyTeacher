"""Утилиты для работы с математическими формулами"""

import re
from typing import List, Tuple, Dict

class FormulaProcessor:
    """Обработчик математических формул в тексте"""
    
    # Регулярные выражения для поиска формул
    INLINE_MATH_PATTERN = r'\$([^$]+)\$'          # $формула$
    DISPLAY_MATH_PATTERN = r'\$\$([^$]+)\$\$'     # $$формула$$
    
    def __init__(self):
        self.inline_pattern = re.compile(self.INLINE_MATH_PATTERN)
        self.display_pattern = re.compile(self.DISPLAY_MATH_PATTERN)

    def has_math(self, text: str) -> bool:
        """Быстрая проверка есть ли в тексте формулы"""
        if not text:
            return False
        
        return bool(self.inline_pattern.search(text) or self.display_pattern.search(text))

    def count_formulas(self, text: str) -> int:
        """Подсчитывает количество формул в тексте"""
        if not text:
            return 0
        
        # Считаем display формулы ($$...$$) 
        display_count = len(self.display_pattern.findall(text))
        
        # Считаем inline формулы ($...$), исключая те что внутри display
        temp_text = self.display_pattern.sub('', text)  # Убираем display формулы
        inline_count = len(self.inline_pattern.findall(temp_text))
        
        return display_count + inline_count
    
    def parse_text(self, text: str) -> Dict[str, any]:
        """Парсит текст и извлекает формулы"""
        if not text:
            return {
                'original_text': text,
                'has_math': False,
                'inline_formulas': [],
                'display_formulas': [],
                'processed_text': text
            }
        
        # Ищем display формулы ($$...$$) - обрабатываем первыми
        display_formulas = []
        display_matches = list(self.display_pattern.finditer(text))
        
        for i, match in enumerate(display_matches):
            formula_id = f"DISPLAY_MATH_{i}"
            display_formulas.append({
                'id': formula_id,
                'content': match.group(1).strip(),
                'original': match.group(0),
                'type': 'display'
            })
        
        # Ищем inline формулы ($...$)
        inline_formulas = []
        inline_matches = list(self.inline_pattern.finditer(text))
        
        for i, match in enumerate(inline_matches):
            # Проверяем что это не часть display формулы
            in_display = False
            for display_match in display_matches:
                if (match.start() >= display_match.start() and 
                    match.end() <= display_match.end()):
                    in_display = True
                    break
            
            if not in_display:
                formula_id = f"INLINE_MATH_{i}"
                inline_formulas.append({
                    'id': formula_id,
                    'content': match.group(1).strip(),
                    'original': match.group(0),
                    'type': 'inline'
                })
        
        # Создаем обработанный текст с плейсхолдерами
        processed_text = text
        
        # Заменяем display формулы
        for formula in display_formulas:
            processed_text = processed_text.replace(
                formula['original'], 
                f"[{formula['id']}]"
            )
        
        # Заменяем inline формулы
        for formula in inline_formulas:
            processed_text = processed_text.replace(
                formula['original'], 
                f"[{formula['id']}]"
            )
        
        return {
            'original_text': text,
            'has_math': bool(display_formulas or inline_formulas),
            'inline_formulas': inline_formulas,
            'display_formulas': display_formulas,
            'processed_text': processed_text,
            'total_formulas': len(display_formulas) + len(inline_formulas)
        }
    
    def validate_latex(self, latex_content: str) -> Dict[str, any]:
        """Простая валидация LaTeX синтаксиса"""
        errors = []
        warnings = []
        
        # Проверяем парные скобки
        brackets = {'{': '}', '[': ']', '(': ')'}
        stack = []
        
        for i, char in enumerate(latex_content):
            if char in brackets.keys():
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    errors.append(f"Непарная закрывающая скобка '{char}' в позиции {i}")
                else:
                    opening, pos = stack.pop()
                    if brackets[opening] != char:
                        errors.append(f"Неправильная пара скобок: '{opening}' в позиции {pos} и '{char}' в позиции {i}")
        
        # Проверяем незакрытые скобки
        for opening, pos in stack:
            errors.append(f"Незакрытая скобка '{opening}' в позиции {pos}")
        
        # Проверяем основные LaTeX команды
        common_commands = [
            r'\\frac', r'\\sqrt', r'\\sum', r'\\int', r'\\lim',
            r'\\sin', r'\\cos', r'\\tan', r'\\log', r'\\ln'
        ]
        
        found_commands = []
        for cmd in common_commands:
            if re.search(cmd, latex_content):
                found_commands.append(cmd.replace('\\\\', '\\'))
        
        # Проверяем потенциально опасные команды
        dangerous_commands = [r'\\input', r'\\include', r'\\write', r'\\immediate']
        
        for cmd in dangerous_commands:
            if re.search(cmd, latex_content):
                errors.append(f"Опасная команда {cmd.replace('\\\\', '\\')} не разрешена")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'found_commands': found_commands,
            'complexity_score': len(found_commands)
        }
    
    def render_for_mathjax(self, text: str) -> str:
        """Подготавливает текст для рендеринга в MathJax"""
        if not text:
            return text
        
        # MathJax понимает $ и $$ нативно, просто возвращаем исходный текст
        return text
    
    def render_for_latex(self, text: str) -> str:
        """Подготавливает текст для LaTeX компиляции"""
        if not text:
            return text
        
        # В LaTeX нужно экранировать некоторые символы
        processed = text
        
        # Заменяем $...$ на \(...\) для inline math
        processed = re.sub(
            self.INLINE_MATH_PATTERN, 
            r'\\(\1\\)', 
            processed
        )
        
        # Заменяем $$...$$ на \[...\] для display math
        processed = re.sub(
            self.DISPLAY_MATH_PATTERN, 
            r'\\[\1\\]', 
            processed
        )
        
        return processed

# Создаем глобальный экземпляр
formula_processor = FormulaProcessor()
