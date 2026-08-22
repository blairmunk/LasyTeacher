"""LaTeX-safe payload formatting for sectioned documents."""

from infrastructure.services.latex_formula_processor import (
    latex_formula_processor,
)


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

    def format_task_payload(self, payload, request=None):
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

        formatted_images = []
        for image in formatted_payload.get('images', ()):
            image_payload = dict(image)
            processed_caption = self.formula_processor.render_for_latex_safe(
                image_payload.get('caption') or '',
            )
            image_payload['caption'] = processed_caption['content']
            formula_errors.extend(processed_caption['errors'])
            formula_warnings.extend(processed_caption['warnings'])
            formatted_images.append(image_payload)
        formatted_payload['images'] = tuple(formatted_images)
        formatted_payload['right_images'] = tuple(
            image
            for image in formatted_images
            if image.get('placement') == 'right'
        )
        formatted_payload['bottom_images'] = tuple(
            image
            for image in formatted_images
            if image.get('placement') == 'bottom'
        )

        formatted_payload['latex_content'] = formatted_payload['text']
        formatted_payload['formula_errors'] = formula_errors
        formatted_payload['formula_warnings'] = formula_warnings
        formatted_payload['has_formula_errors'] = bool(formula_errors)
        formatted_payload['has_formula_warnings'] = bool(formula_warnings)
        return formatted_payload


class RenderTargetTaskPayloadFormatter:
    def __init__(
        self,
        formatters_by_renderer_type=None,
        default_formatter=None,
        base_formatter=None,
    ):
        self.formatters_by_renderer_type = formatters_by_renderer_type or {}
        self.default_formatter = default_formatter
        self.base_formatter = base_formatter

    def format_task_payload(self, payload, request=None):
        if self.base_formatter is not None:
            payload = self.base_formatter.format_task_payload(
                payload,
                request=request,
            )
        formatter = self._formatter_for(request)
        if formatter is None:
            return dict(payload)
        return formatter.format_task_payload(payload, request=request)

    def _formatter_for(self, request):
        if request is None or request.render_target is None:
            return self.default_formatter
        return (
            self.formatters_by_renderer_type.get(
                request.render_target.renderer_type,
            )
            or self.default_formatter
        )
