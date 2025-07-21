"""Утилиты для работы с математическими формулами с обработкой ошибок"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from django.utils.html import escape

logger = logging.getLogger(__name__)

class FormulaValidationError(Exception):
    """Ошибка валидации формулы"""
    pass

class FormulaProcessor:
    """Обработчик математических формул в тексте с валидацией"""
    
    # Регулярные выражения для поиска формул
    INLINE_MATH_PATTERN = r'\$([^$]+)\$'          # $формула$
    DISPLAY_MATH_PATTERN = r'\$\$([^$]+)\$\$'     # $$формула$$
    
    # Список разрешенных LaTeX команд (белый список)
    ALLOWED_COMMANDS = {
        # Математические операторы
        r'\\frac', r'\\sqrt', r'\\sum', r'\\prod', r'\\int', r'\\oint',
        r'\\lim', r'\\sup', r'\\inf', r'\\max', r'\\min', r'\\gcd',
        
        # Тригонометрические функции
        r'\\sin', r'\\cos', r'\\tan', r'\\cot', r'\\sec', r'\\csc',
        r'\\arcsin', r'\\arccos', r'\\arctan',
        
        # Логарифмы и экспоненты
        r'\\log', r'\\ln', r'\\lg', r'\\exp',
        
        # Греческие буквы
        r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\epsilon', r'\\zeta',
        r'\\eta', r'\\theta', r'\\iota', r'\\kappa', r'\\lambda', r'\\mu',
        r'\\nu', r'\\xi', r'\\pi', r'\\rho', r'\\sigma', r'\\tau',
        r'\\upsilon', r'\\phi', r'\\chi', r'\\psi', r'\\omega',
        r'\\Gamma', r'\\Delta', r'\\Theta', r'\\Lambda', r'\\Xi',
        r'\\Pi', r'\\Sigma', r'\\Upsilon', r'\\Phi', r'\\Psi', r'\\Omega',
        
        # Математические символы
        r'\\pm', r'\\mp', r'\\times', r'\\div', r'\\cdot', r'\\ast',
        r'\\leq', r'\\geq', r'\\neq', r'\\approx', r'\\equiv', r'\\sim',
        r'\\propto', r'\\parallel', r'\\perp', r'\\subset', r'\\supset',
        r'\\in', r'\\notin', r'\\cup', r'\\cap', r'\\emptyset', r'\\infty',
        
        # Стрелки
        r'\\rightarrow', r'\\leftarrow', r'\\leftrightarrow',
        r'\\Rightarrow', r'\\Leftarrow', r'\\Leftrightarrow',
        
        # Скобки и разделители
        r'\\left', r'\\right', r'\\big', r'\\Big', r'\\bigg', r'\\Bigg',
        
        # Текст и пробелы
        r'\\text', r'\\mathrm', r'\\mathit', r'\\mathbf', r'\\mathbb',
        r'\\quad', r'\\qquad', r'\\,', r'\\:', r'\\;', r'\\ ',
        
        # Индексы и степени (неявно разрешены через ^ и _)
        
        # Матрицы и системы
        r'\\begin', r'\\end', r'\\matrix', r'\\pmatrix', r'\\bmatrix',
        r'\\vmatrix', r'\\Vmatrix', r'\\cases', r'\\split', r'\\align',
        
        # Символы множеств
        r'\\mathbb', r'\\mathcal', r'\\mathfrak',
    }
    
    # Опасные команды (черный список)
    DANGEROUS_COMMANDS = {
        r'\\input', r'\\include', r'\\write', r'\\immediate', r'\\openout',
        r'\\closeout', r'\\read', r'\\readline', r'\\catcode', r'\\def',
        r'\\let', r'\\expandafter', r'\\csname', r'\\endcsname', r'\\the',
        r'\\jobname', r'\\meaning', r'\\string', r'\\detokenize',
        r'\\scantokens', r'\\directlua', r'\\luaexec',
    }
    
    def __init__(self):
        self.inline_pattern = re.compile(self.INLINE_MATH_PATTERN)
        self.display_pattern = re.compile(self.DISPLAY_MATH_PATTERN)
        
        # Компилируем регулярки для команд
        self.allowed_commands_pattern = re.compile('|'.join(self.ALLOWED_COMMANDS))
        self.dangerous_commands_pattern = re.compile('|'.join(self.DANGEROUS_COMMANDS))
    
    def validate_formula_security(self, formula: str) -> Dict[str, any]:
        """Проверяет формулу на безопасность"""
        errors = []
        warnings = []
        
        # Проверяем на опасные команды
        dangerous_matches = list(self.dangerous_commands_pattern.finditer(formula))
        for match in dangerous_matches:
            cmd = match.group()
            errors.append(f"Опасная команда {cmd} не разрешена из соображений безопасности")
        
        # Проверяем парные скобки
        bracket_pairs = {'{': '}', '[': ']', '(': ')'}
        stack = []
        
        for i, char in enumerate(formula):
            if char in bracket_pairs:
                stack.append((char, i))
            elif char in bracket_pairs.values():
                if not stack:
                    errors.append(f"Непарная закрывающая скобка '{char}' в позиции {i}")
                else:
                    opening, pos = stack.pop()
                    if bracket_pairs[opening] != char:
                        errors.append(f"Неправильная пара скобок: '{opening}' (поз. {pos}) и '{char}' (поз. {i})")
        
        # Незакрытые скобки
        for opening, pos in stack:
            errors.append(f"Незакрытая скобка '{opening}' в позиции {pos}")
        
        # Проверяем длину формулы (защита от DoS)
        if len(formula) > 1000:
            warnings.append("Формула очень длинная, это может замедлить рендеринг")
        
        # Проверяем вложенность команд (защита от DoS)
        nesting_level = 0
        max_nesting = 0
        for char in formula:
            if char == '{':
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)
            elif char == '}':
                nesting_level -= 1
        
        if max_nesting > 20:
            warnings.append("Слишком глубокая вложенность команд")
        
        return {
            'is_safe': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'max_nesting': max_nesting
        }
    
    def validate_formula_syntax(self, formula: str) -> Dict[str, any]:
        """Проверяет синтаксис формулы"""
        errors = []
        warnings = []
        
        # Проверяем базовые LaTeX конструкции
        # Проверяем \frac{}{} 
        frac_pattern = r'\\frac\s*\{[^}]*\}\s*\{[^}]*\}'
        incomplete_frac = r'\\frac(?!\s*\{[^}]*\}\s*\{[^}]*\})'
        
        if re.search(incomplete_frac, formula):
            errors.append("Неполная команда \\frac - должна быть \\frac{числитель}{знаменатель}")
        
        # Проверяем \sqrt{}
        sqrt_pattern = r'\\sqrt(?:\[[^\]]*\])?\s*\{[^}]*\}'
        incomplete_sqrt = r'\\sqrt(?!(?:\[[^\]]*\])?\s*\{)'
        
        if re.search(incomplete_sqrt, formula):
            errors.append("Неполная команда \\sqrt - должна быть \\sqrt{выражение}")
        
        # Проверяем парность \left и \right
        left_count = len(re.findall(r'\\left', formula))
        right_count = len(re.findall(r'\\right', formula))
        
        if left_count != right_count:
            errors.append(f"Несоответствие количества \\left ({left_count}) и \\right ({right_count})")
        
        # Проверяем матричные окружения
        matrix_envs = ['matrix', 'pmatrix', 'bmatrix', 'vmatrix', 'Vmatrix', 'cases']
        for env in matrix_envs:
            begin_pattern = f'\\\\begin{{{env}}}'
            end_pattern = f'\\\\end{{{env}}}'
            
            begin_count = len(re.findall(begin_pattern, formula))
            end_count = len(re.findall(end_pattern, formula))
            
            if begin_count != end_count:
                errors.append(f"Несоответствие \\begin{{{env}}} ({begin_count}) и \\end{{{env}}} ({end_count})")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def safe_validate_formula(self, formula: str) -> Dict[str, any]:
        """Комплексная валидация формулы"""
        try:
            # Проверяем безопасность
            security_result = self.validate_formula_security(formula)
            
            # Проверяем синтаксис (только если безопасно)
            if security_result['is_safe']:
                syntax_result = self.validate_formula_syntax(formula)
            else:
                syntax_result = {'is_valid': False, 'errors': [], 'warnings': []}
            
            return {
                'is_valid': security_result['is_safe'] and syntax_result['is_valid'],
                'is_safe': security_result['is_safe'],
                'errors': security_result['errors'] + syntax_result['errors'],
                'warnings': security_result['warnings'] + syntax_result['warnings'],
                'formula': formula
            }
            
        except Exception as e:
            logger.error(f"Ошибка при валидации формулы '{formula}': {e}")
            return {
                'is_valid': False,
                'is_safe': False,
                'errors': [f"Внутренняя ошибка валидации: {str(e)}"],
                'warnings': [],
                'formula': formula
            }
    
    def process_text_safe(self, text: str) -> Dict[str, any]:
        """Безопасная обработка текста с формулами"""
        if not text:
            return {
                'original_text': text,
                'has_math': False,
                'processed_text': text,
                'errors': [],
                'warnings': [],
                'formulas': []
            }
        
        all_errors = []
        all_warnings = []
        all_formulas = []
        
        # Обрабатываем display формулы
        display_matches = list(self.display_pattern.finditer(text))
        for match in display_matches:
            formula = match.group(1).strip()
            validation = self.safe_validate_formula(formula)
            
            all_formulas.append({
                'type': 'display',
                'content': formula,
                'original': match.group(0),
                'validation': validation,
                'position': (match.start(), match.end())
            })
            
            all_errors.extend(validation['errors'])
            all_warnings.extend(validation['warnings'])
        
        # Обрабатываем inline формулы (исключаем те что в display)
        temp_text = text
        for match in display_matches:
            temp_text = temp_text.replace(match.group(0), ' ' * len(match.group(0)))
        
        inline_matches = list(self.inline_pattern.finditer(temp_text))
        for match in inline_matches:
            formula = match.group(1).strip()
            validation = self.safe_validate_formula(formula)
            
            all_formulas.append({
                'type': 'inline',
                'content': formula,
                'original': text[match.start():match.end()],  # Берем из оригинального текста
                'validation': validation,
                'position': (match.start(), match.end())
            })
            
            all_errors.extend(validation['errors'])
            all_warnings.extend(validation['warnings'])
        
        return {
            'original_text': text,
            'has_math': len(all_formulas) > 0,
            'processed_text': text,  # Пока оставляем как есть
            'errors': all_errors,
            'warnings': all_warnings,
            'formulas': all_formulas,
            'total_formulas': len(all_formulas),
            'has_errors': len(all_errors) > 0,
            'has_warnings': len(all_warnings) > 0
        }
    
    def render_for_latex_safe(self, text: str) -> Dict[str, any]:
        """КАРДИНАЛЬНО ИСПРАВЛЕНО: Безопасное преобразование для LaTeX компиляции"""
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



    def _sanitize_dangerous_latex_completely(self, text: str) -> str:
        """УЛУЧШЕНО: Полная очистка от опасных LaTeX команд ВНЕ математических окружений"""
        if not text:
            return text
        
        # НЕ трогаем уже обработанные математические окружения \(...\) и \[...\]
        # Они уже безопасны
        
        # Опасные команды только ВНЕ математических окружений
        dangerous_patterns = [
            r'\\input\{[^}]*\}',           # \input{файл}
            r'\\include\{[^}]*\}',         # \include{файл}  
            r'\\write\d*\{[^}]*\}',        # \write18{команда}
            r'\\immediate\b',              # \immediate
            r'\\openout\d*\{[^}]*\}',      # \openout
            r'\\closeout\d*',              # \closeout
            r'\\read\d*',                  # \read
            r'\\catcode[^\s]*',            # \catcode
            r'\\def\\[^\s]*\{[^}]*\}',     # \def
            r'\\let\\[^\s]*',              # \let
            r'\\csname[^\\]*\\endcsname',  # \csname
            r'\\expandafter\b',            # \expandafter
            r'\\the\\[^\s]*',              # \the
            r'\\jobname\b',                # \jobname
            r'\\meaning\b',                # \meaning
            r'\\string\b',                 # \string
            r'\\detokenize\{[^}]*\}',      # \detokenize
            r'\\scantokens\{[^}]*\}',      # \scantokens
            r'\\directlua\{[^}]*\}',       # \directlua (LuaTeX)
            r'\\luaexec\{[^}]*\}',         # \luaexec
        ]
        
        clean_text = text
        replacements_made = []
        
        # Сначала найдем все математические окружения чтобы их не трогать
        math_ranges = []
        
        # Находим \(...\) окружения
        for match in re.finditer(r'\\\\?\((.*?)\\\\?\)', clean_text):
            math_ranges.append((match.start(), match.end()))
        
        # Находим \[...\] окружения  
        for match in re.finditer(r'\\\\?\[(.*?)\\\\?\]', clean_text):
            math_ranges.append((match.start(), match.end()))
        
        # Сортируем диапазоны
        math_ranges.sort()
        
        for pattern in dangerous_patterns:
            matches = list(re.finditer(pattern, clean_text, re.IGNORECASE))
            
            for match in matches:
                # Проверяем что команда НЕ внутри математического окружения
                in_math = False
                for start, end in math_ranges:
                    if start <= match.start() < end:
                        in_math = True
                        break
                
                if not in_math:
                    replacements_made.append(match.group())
                    # Заменяем на безопасный текст
                    clean_text = clean_text.replace(match.group(), '\\textbf{[ЗАБЛОКИРОВАНО]}', 1)
        
        if replacements_made:
            logger.warning(f"Заблокированы опасные команды: {replacements_made}")
        
        return clean_text


    
    # Сохраняем старые методы для обратной совместимости
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

# Создаем глобальный экземпляр
formula_processor = FormulaProcessor()
