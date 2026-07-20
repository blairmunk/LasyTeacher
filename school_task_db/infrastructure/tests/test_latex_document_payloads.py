from django.test import SimpleTestCase

from core_logic.value_objects.document_render_options import RenderTarget
from infrastructure.services.latex_formula_processor import (
    latex_formula_processor,
    sanitize_latex,
)
from infrastructure.services.latex_document_payloads import (
    LatexTaskPayloadFormatter,
    RenderTargetTaskPayloadFormatter,
)


class LatexTaskPayloadFormatterTests(SimpleTestCase):
    def test_sanitize_latex_escapes_text_control_characters(self):
        result = sanitize_latex('Цена $5 & скидка 10%')

        self.assertEqual(result, r'Цена \$5 \& скидка 10\%')

    def test_latex_formula_processor_preserves_math_blocks(self):
        result = latex_formula_processor.render_for_latex_safe(
            'Сила & формула $F=ma$',
        )

        self.assertEqual(
            result['content'],
            r'Сила \& формула \(F=ma\)',
        )
        self.assertEqual(result['errors'], [])

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

    def test_render_target_formatter_applies_formatter_for_matching_target(self):
        latex_formatter = FakeTaskPayloadFormatter(label='latex')
        formatter = RenderTargetTaskPayloadFormatter(
            formatters_by_renderer_type={'latex': latex_formatter},
        )

        html_payload = formatter.format_task_payload(
            {'text': 'HTML'},
            request=FakePayloadBuildRequest(renderer_type='html'),
        )
        latex_payload = formatter.format_task_payload(
            {'text': 'LaTeX'},
            request=FakePayloadBuildRequest(renderer_type='latex'),
        )

        self.assertEqual(html_payload, {'text': 'HTML'})
        self.assertEqual(latex_payload, {'text': 'LaTeX', 'formatted_as': 'latex'})
        self.assertEqual(latex_formatter.requests[0].render_target.renderer_type, 'latex')


class FakeFormulaProcessor:
    def render_for_latex_safe(self, text):
        return {
            'content': f'<latex>{text}</latex>',
            'errors': [f'error:{text}'] if '$' in text else [],
            'warnings': [f'warning:{text}'] if '&' in text else [],
        }


class FakePayloadBuildRequest:
    def __init__(self, renderer_type):
        self.render_target = RenderTarget(renderer_type=renderer_type)


class FakeTaskPayloadFormatter:
    def __init__(self, label):
        self.label = label
        self.requests = []

    def format_task_payload(self, payload, request=None):
        self.requests.append(request)
        return {
            **payload,
            'formatted_as': self.label,
        }
