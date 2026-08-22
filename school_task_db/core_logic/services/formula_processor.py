"""Common parsing and validation for formulas embedded in task text."""

import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FormulaProcessor:
    """Процессор математических формул с валидацией и обработкой ошибок"""
    
    # Опасные LaTeX команды
    DANGEROUS_COMMANDS = {
        r'\\input\{[^}]*\}': 'Опасная команда \\input не разрешена из соображений безопасности',
        r'\\include\{[^}]*\}': 'Опасная команда \\include не разрешена из соображений безопасности',
        r'\\write\d*\{[^}]*\}': 'Опасная команда \\write не разрешена из соображений безопасности',
        r'\\immediate\b': 'Опасная команда \\immediate не разрешена из соображений безопасности',
        r'\\openout\d*\{[^}]*\}': 'Опасная команда \\openout не разрешена из соображений безопасности',
        r'\\closeout\d*': 'Опасная команда \\closeout не разрешена из соображений безопасности',
        r'\\read\d*': 'Опасная команда \\read не разрешена из соображений безопасности',
        r'\\def\\[^\s]*\{[^}]*\}': 'Опасная команда \\def не разрешена из соображений безопасности',
        r'\\let\\[^\s]*': 'Опасная команда \\let не разрешена из соображений безопасности',
        r'\\csname[^\\]*\\endcsname': 'Опасная команда \\csname не разрешена из соображений безопасности',
        r'\\expandafter\b': 'Опасная команда \\expandafter не разрешена из соображений безопасности',
        r'\\directlua\{[^}]*\}': 'Опасная команда \\directlua не разрешена из соображений безопасности',
    }
    
    def has_math(self, text: str) -> bool:
        """Проверяет содержит ли текст математические формулы"""
        return bool(self.extract_formulas(text))
    
    def count_formulas(self, text: str) -> int:
        """Подсчитать количество формул в тексте."""
        return len(self.extract_formulas(text))

    def render_for_latex_safe(self, text: str) -> Dict[str, Any]:
        """Сформировать безопасный LaTeX в форматном адаптере."""
        raise NotImplementedError(
            'Используйте специфичную реализацию для формата',
        )

    def render_for_html_safe(self, text: str) -> Dict[str, Any]:
        """Сформировать безопасный HTML-текст для MathJax."""
        if not text:
            return {'content': text, 'errors': [], 'warnings': []}
        
        # Для HTML мы НЕ преобразуем $ в LaTeX команды
        # MathJax обработает $ и $$ автоматически
        processed = self.process_text_safe(text)
        
        if processed['has_errors']:
            # Заменяем только проблемные формулы
            safe_text = text
            
            for formula in processed['formulas']:
                if not formula['validation']['is_valid']:
                    errors = formula['validation']['errors']
                    
                    if any('опасная команда' in error.lower() for error in errors):
                        # HTML безопасная замена
                        safe_replacement = '<span class="blocked-formula">[ЗАБЛОКИРОВАННАЯ КОМАНДА]</span>'
                    else:
                        error_count = len(errors)
                        safe_replacement = f'<span class="formula-error" title="{"; ".join(errors)}">[ОШИБКА: {error_count} проблем]</span>'
                    
                    safe_text = safe_text.replace(formula['original'], safe_replacement)
            
            return {
                'content': safe_text,
                'errors': processed['errors'],
                'warnings': processed['warnings']
            }
        else:
            # Возвращаем текст как есть - MathJax обработает формулы
            return {
                'content': text,
                'errors': [],
                'warnings': processed['warnings']
            }

    def extract_formulas(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает все математические формулы из текста"""
        if not text:
            return []

        formulas = []
        cursor = 0
        while cursor < len(text):
            opening = self._opening_delimiter(text, cursor)
            if opening is None:
                cursor += 1
                continue

            opening_delimiter, closing_delimiter, formula_type = opening
            content_start = cursor + len(opening_delimiter)
            closing_start = self._find_closing_delimiter(
                text,
                content_start,
                closing_delimiter,
            )
            if closing_start is None:
                cursor += len(opening_delimiter)
                continue

            end = closing_start + len(closing_delimiter)
            formulas.append({
                'type': formula_type,
                'content': text[content_start:closing_start],
                'original': text[cursor:end],
                'position': (cursor, end),
            })
            cursor = end
        return formulas

    def _opening_delimiter(self, text: str, position: int):
        if self._is_escaped(text, position):
            return None
        if text.startswith('$$', position):
            return '$$', '$$', 'display'
        if text[position] == '$':
            return '$', '$', 'inline'
        if text.startswith(r'\(', position):
            return r'\(', r'\)', 'inline'
        if text.startswith(r'\[', position):
            return r'\[', r'\]', 'display'
        return None

    def _find_closing_delimiter(
        self,
        text: str,
        start: int,
        delimiter: str,
    ):
        position = start
        while position < len(text):
            if (
                text.startswith(delimiter, position)
                and not self._is_escaped(text, position)
            ):
                if delimiter == '$' and text.startswith('$$', position):
                    position += 2
                    continue
                return position
            position += 1
        return None

    @staticmethod
    def _is_escaped(text: str, position: int) -> bool:
        backslashes = 0
        position -= 1
        while position >= 0 and text[position] == '\\':
            backslashes += 1
            position -= 1
        return backslashes % 2 == 1

    def validate_formula(self, formula_content: str) -> Dict[str, Any]:
        """Валидирует математическую формулу"""
        errors = []
        warnings = []
        
        if not formula_content:
            errors.append("Пустая формула")
            return {
                'is_valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        # Проверка опасных команд
        for pattern, error_message in self.DANGEROUS_COMMANDS.items():
            if re.search(pattern, formula_content, re.IGNORECASE):
                errors.append(error_message)
        
        # Проверка сбалансированности скобок
        bracket_pairs = [('(', ')'), ('{', '}'), ('[', ']')]
        for open_br, close_br in bracket_pairs:
            open_count = formula_content.count(open_br)
            close_count = formula_content.count(close_br)
            if open_count != close_count:
                errors.append(f"Несбалансированные скобки: {open_br}{close_br}")
        
        # Проверка \left \right команд
        left_count = len(re.findall(r'\\left\b', formula_content))
        right_count = len(re.findall(r'\\right\b', formula_content))
        if left_count != right_count:
            errors.append("Несбалансированные \\left и \\right команды")
        
        # Проверка незакрытых \begin{} команд
        begin_matches = re.findall(r'\\begin\{([^}]+)\}', formula_content)
        for env_name in begin_matches:
            end_pattern = rf'\\end\{{{re.escape(env_name)}\}}'
            if not re.search(end_pattern, formula_content):
                errors.append(f"Незакрытое окружение \\begin{{{env_name}}}")
        
        # Предупреждения о сложности
        nesting_level = self._calculate_nesting_level(formula_content)
        if nesting_level > 10:
            warnings.append(f"Глубокая вложенность команд ({nesting_level} уровней)")
        
        formula_length = len(formula_content)
        if formula_length > 200:
            warnings.append(f"Очень длинная формула ({formula_length} символов)")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _calculate_nesting_level(self, text: str) -> int:
        """Вычисляет уровень вложенности команд"""
        max_level = 0
        current_level = 0
        
        i = 0
        while i < len(text):
            if text[i] == '{':
                current_level += 1
                max_level = max(max_level, current_level)
            elif text[i] == '}':
                current_level = max(0, current_level - 1)
            elif text[i:i+6] == '\\frac{':
                current_level += 2  # \frac добавляет 2 уровня вложенности
                max_level = max(max_level, current_level)
                i += 5  # Пропускаем \frac
            i += 1
        
        return max_level

    def process_text_safe(self, text: str) -> Dict[str, Any]:
        """Безопасно обрабатывает текст с формулами"""
        if not text:
            return {
                'has_math': False,
                'formulas': [],
                'errors': [],
                'warnings': [],
                'has_errors': False,
                'has_warnings': False,
                'total_formulas': 0
            }
        
        formulas = self.extract_formulas(text)
        all_errors = []
        all_warnings = []
        
        for formula in formulas:
            validation = self.validate_formula(formula['content'])
            formula['validation'] = validation
            all_errors.extend(validation['errors'])
            all_warnings.extend(validation['warnings'])
        
        return {
            'has_math': len(formulas) > 0,
            'formulas': formulas,
            'errors': all_errors,
            'warnings': all_warnings,
            'has_errors': len(all_errors) > 0,
            'has_warnings': len(all_warnings) > 0,
            'total_formulas': len(formulas)
        }

    def _sanitize_dangerous_latex_completely(self, text: str) -> str:
        """Полная очистка от опасных LaTeX команд"""
        if not text:
            return text
        
        dangerous_patterns = [
            r'\\input\{[^}]*\}',
            r'\\include\{[^}]*\}', 
            r'\\write\d*\{[^}]*\}',
            r'\\immediate\b',
            r'\\openout\d*\{[^}]*\}',
            r'\\closeout\d*',
            r'\\read\d*',
            r'\\catcode[^\s]*',
            r'\\def\\[^\s]*\{[^}]*\}',
            r'\\let\\[^\s]*',
            r'\\csname[^\\]*\\endcsname',
            r'\\expandafter\b',
            r'\\the\\[^\s]*',
            r'\\jobname\b',
            r'\\meaning\b',
            r'\\string\b',
            r'\\detokenize\{[^}]*\}',
            r'\\scantokens\{[^}]*\}',
            r'\\directlua\{[^}]*\}',
            r'\\luaexec\{[^}]*\}',
        ]
        
        clean_text = text
        replacements_made = []
        
        for pattern in dangerous_patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    replacements_made.append(match)
                    clean_text = clean_text.replace(match, '[ЗАБЛОКИРОВАНО]')
        
        if replacements_made:
            logger.warning(f"Заблокированы опасные команды: {replacements_made}")
        
        return clean_text


# Глобальный экземпляр процессора формул
formula_processor = FormulaProcessor()


def render_math_safe(text: str) -> str:
    if not text:
        return ''
    processed = formula_processor.render_for_html_safe(text)
    return processed['content']


def get_formula_errors(text: str) -> List[str]:
    processed = formula_processor.process_text_safe(text)
    return processed['errors']


def has_formula_errors(text: str) -> bool:
    return bool(get_formula_errors(text))
