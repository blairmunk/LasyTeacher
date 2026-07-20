from django.test import SimpleTestCase

from infrastructure.services.latex_document_payloads import (
    LatexTaskPayloadFormatter,
)


class LatexTaskPayloadFormatterTests(SimpleTestCase):
    def test_formats_task_text_fields_for_latex(self):
        formatter = LatexTaskPayloadFormatter(
            formula_processor=FakeFormulaProcessor(),
        )
        payload = {
            'text': 'Text & $x$',
            'answer': 'Answer',
            'short_solution': '',
            'full_solution': None,
            'hint': 'Hint',
            'instruction': 'Instruction',
            'difficulty': 2,
        }

        formatted = formatter.format_task_payload(payload)

        self.assertEqual(payload['text'], 'Text & $x$')
        self.assertEqual(formatted['text'], '<latex>Text & $x$</latex>')
        self.assertEqual(formatted['answer'], '<latex>Answer</latex>')
        self.assertEqual(formatted['short_solution'], '<latex></latex>')
        self.assertEqual(formatted['full_solution'], '<latex></latex>')
        self.assertEqual(formatted['hint'], '<latex>Hint</latex>')
        self.assertEqual(formatted['instruction'], '<latex>Instruction</latex>')
        self.assertEqual(formatted['latex_content'], formatted['text'])
        self.assertEqual(formatted['difficulty'], 2)
        self.assertEqual(
            formatted['formula_errors'],
            ['error:Text & $x$'],
        )
        self.assertEqual(
            formatted['formula_warnings'],
            ['warning:Text & $x$'],
        )
        self.assertTrue(formatted['has_formula_errors'])
        self.assertTrue(formatted['has_formula_warnings'])


class FakeFormulaProcessor:
    def render_for_latex_safe(self, text):
        return {
            'content': f'<latex>{text}</latex>',
            'errors': [f'error:{text}'] if '$' in text else [],
            'warnings': [f'warning:{text}'] if '&' in text else [],
        }
