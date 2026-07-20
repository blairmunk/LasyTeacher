"""LaTeX formula processing for sectioned document rendering."""

import re
from typing import Any

from core_logic.services.formula_processor import (
    formula_processor as base_processor,
)


def sanitize_latex(text):
    if not text:
        return ''

    result = text.replace('\\', r'\textbackslash{}')
    replacements = {
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '~': r'\textasciitilde{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    return result.replace('\n', '\\\\ ')


class LaTeXFormulaProcessor:
    def __init__(self, base_formula_processor=None):
        self.base_processor = base_formula_processor or base_processor

    def render_for_latex_safe(self, text: str) -> dict[str, Any]:
        if not text:
            return {'content': text, 'errors': [], 'warnings': []}

        processed = self.process_text_safe(text)
        if not processed['has_math']:
            cleaned_text = self._sanitize_dangerous_latex_completely(text)
            return {
                'content': sanitize_latex(cleaned_text),
                'errors': [],
                'warnings': [],
            }

        safe_text = text
        all_errors = []
        all_warnings = []
        formulas_by_position = sorted(
            processed['formulas'],
            key=lambda formula: formula['position'][0],
            reverse=True,
        )

        for formula in formulas_by_position:
            start, end = formula['position']

            if not formula['validation']['is_valid']:
                errors = formula['validation']['errors']
                if any('опасная команда' in error.lower() for error in errors):
                    replacement = r'\textbf{[ЗАБЛОКИРОВАННАЯ КОМАНДА]}'
                else:
                    replacement = (
                        r'\textbf{[ОШИБКА: '
                        f'{len(errors)}'
                        r' проблем]}'
                    )
                all_errors.extend(formula['validation']['errors'])
                all_warnings.extend(formula['validation']['warnings'])
            elif formula['type'] == 'display':
                replacement = f"\\[{formula['content']}\\]"
            else:
                replacement = f"\\({formula['content']}\\)"

            safe_text = safe_text[:start] + replacement + safe_text[end:]

        safe_text = self._sanitize_dangerous_latex_completely(safe_text)
        safe_text = self._smart_sanitize_latex(safe_text)
        return {
            'content': safe_text,
            'errors': all_errors,
            'warnings': all_warnings,
        }

    def _smart_sanitize_latex(self, text: str) -> str:
        if not text:
            return text

        math_placeholders = {}
        placeholder_counter = 0
        temp_text = text

        def save_latex_math(match):
            nonlocal placeholder_counter
            placeholder = f'LATEXMATHBLOCK{placeholder_counter}LATEXMATHBLOCK'
            math_placeholders[placeholder] = match.group(0)
            placeholder_counter += 1
            return placeholder

        temp_text = re.sub(r'\\\([^)]*\\\)', save_latex_math, temp_text)
        temp_text = re.sub(r'\\\[[^\]]*\\\]', save_latex_math, temp_text)
        sanitized_text = sanitize_latex(temp_text)

        for placeholder, original in math_placeholders.items():
            sanitized_text = sanitized_text.replace(placeholder, original)

        return sanitized_text

    def __getattr__(self, name):
        return getattr(self.base_processor, name)


latex_formula_processor = LaTeXFormulaProcessor()
