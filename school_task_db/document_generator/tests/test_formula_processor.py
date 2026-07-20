from unittest import TestCase

from core_logic.services.formula_processor import (
    formula_processor as core_formula_processor,
)
from document_generator.utils.formula_utils import (
    formula_processor as compatibility_formula_processor,
)
from document_generator.processors.formula import process_formula_text


class FormulaProcessorTests(TestCase):
    def test_legacy_formula_utils_reexports_core_processor(self):
        self.assertIs(compatibility_formula_processor, core_formula_processor)

    def test_process_formula_text_returns_processor_result(self):
        def process(text):
            return {
                'content': f'<p>{text}</p>',
                'errors': [],
                'warnings': ['warn'],
            }

        result = process_formula_text('x^2', process, label='task text')

        self.assertEqual(
            result,
            {
                'content': '<p>x^2</p>',
                'errors': [],
                'warnings': ['warn'],
            },
        )

    def test_process_formula_text_returns_empty_result_for_empty_text(self):
        def process(text):
            raise AssertionError('process should not be called')

        result = process_formula_text('', process)

        self.assertEqual(result, {'content': '', 'errors': [], 'warnings': []})

    def test_process_formula_text_falls_back_to_original_text(self):
        def process(text):
            raise ValueError('broken formula')

        with self.assertLogs(
            'document_generator.processors.formula',
            level='ERROR',
        ):
            result = process_formula_text('bad $x$', process, label='answer')

        self.assertEqual(result['content'], 'bad $x$')
        self.assertEqual(result['errors'], ['answer: broken formula'])
        self.assertEqual(result['warnings'], [])
