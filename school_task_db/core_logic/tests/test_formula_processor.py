from unittest import TestCase

from core_logic.services.formula_processor import (
    FormulaProcessor,
    get_formula_errors,
    has_formula_errors,
    render_math_safe,
)


class FormulaProcessorServiceTests(TestCase):
    def test_detects_and_counts_inline_math(self):
        processor = FormulaProcessor()

        self.assertTrue(processor.has_math('Скорость $v=s/t$'))
        self.assertEqual(processor.count_formulas('A $x$ and $y$'), 2)

    def test_reports_dangerous_formula_commands(self):
        errors = get_formula_errors(r'Опасно $\input{secret}$')

        self.assertTrue(has_formula_errors(r'Опасно $\input{secret}$'))
        self.assertIn('Опасная команда', errors[0])

    def test_render_math_safe_keeps_valid_html_math_text(self):
        self.assertEqual(render_math_safe('Формула $x^2$'), 'Формула $x^2$')
