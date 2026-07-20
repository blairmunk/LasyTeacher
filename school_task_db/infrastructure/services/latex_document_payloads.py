"""LaTeX-safe payload formatting for sectioned documents."""

from latex_generator.utils.latex_specific import latex_formula_processor


LATEX_TEXT_FIELDS = (
    'text',
    'answer',
    'short_solution',
    'full_solution',
    'hint',
    'instruction',
)


class LatexTaskPayloadFormatter:
    def __init__(self, formula_processor=None):
        self.formula_processor = formula_processor or latex_formula_processor

    def format_task_payload(self, payload):
        formatted_payload = dict(payload)
        formula_errors = []
        formula_warnings = []

        for field_name in LATEX_TEXT_FIELDS:
            processed = self.formula_processor.render_for_latex_safe(
                formatted_payload.get(field_name) or '',
            )
            formatted_payload[field_name] = processed['content']
            formula_errors.extend(processed['errors'])
            formula_warnings.extend(processed['warnings'])

        formatted_payload['latex_content'] = formatted_payload['text']
        formatted_payload['formula_errors'] = formula_errors
        formatted_payload['formula_warnings'] = formula_warnings
        formatted_payload['has_formula_errors'] = bool(formula_errors)
        formatted_payload['has_formula_warnings'] = bool(formula_warnings)
        return formatted_payload
