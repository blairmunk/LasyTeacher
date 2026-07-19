from unittest import TestCase

from document_generator.processors.formula import process_formula_text


class FormulaProcessorTests(TestCase):
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
