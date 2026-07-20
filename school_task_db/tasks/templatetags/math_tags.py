"""Template tags for rendering and inspecting math formulas in tasks."""

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from core_logic.services.formula_processor import formula_processor

register = template.Library()


@register.filter
def render_math(text):
    if not text:
        return ''
    return mark_safe(text)


@register.filter
def has_math(text):
    return formula_processor.has_math(text)


@register.filter
def has_math_formulas(text):
    if not text:
        return False
    return formula_processor.has_math(text)


@register.filter
def count_formulas(text):
    if not text:
        return 0
    return formula_processor.count_formulas(text)


@register.filter
def math_count(text):
    return formula_processor.count_formulas(text)


@register.filter
def math_errors(text):
    if not text:
        return []
    return formula_processor.process_text_safe(text).get('errors', [])


@register.filter
def math_warnings(text):
    if not text:
        return []
    return formula_processor.process_text_safe(text).get('warnings', [])


@register.filter
def has_math_errors(text):
    if not text:
        return False
    return formula_processor.process_text_safe(text).get('has_errors', False)


@register.filter
def has_math_warnings(text):
    if not text:
        return False
    return formula_processor.process_text_safe(text).get('has_warnings', False)


@register.simple_tag
def math_indicator(text):
    if not formula_processor.has_math(text):
        return ''

    count = formula_processor.count_formulas(text)
    processed = formula_processor.process_text_safe(text)

    if processed.get('has_errors', False):
        badge_class = 'bg-danger'
        icon = '⚠️'
        title = f'Формул: {count}. Есть ошибки!'
    elif processed.get('has_warnings', False):
        badge_class = 'bg-warning text-dark'
        icon = '⚡'
        title = f'Формул: {count}. Есть предупреждения'
    else:
        badge_class = 'bg-success'
        icon = '📐'
        title = f'Формул: {count}. Все корректно'

    return mark_safe(
        f'<span class="badge {badge_class} formula-badge" title="{title}">'
        f'{icon} {count}</span>'
    )


@register.inclusion_tag('math/formula_errors.html')
def show_formula_errors(text, show_warnings=True):
    if not text:
        return {'errors': [], 'warnings': [], 'formulas': []}

    processed = formula_processor.process_text_safe(text)
    return {
        'errors': processed.get('errors', []),
        'warnings': processed.get('warnings', []) if show_warnings else [],
        'formulas': processed.get('formulas', []),
        'has_errors': processed.get('has_errors', False),
        'has_warnings': processed.get('has_warnings', False),
    }


@register.inclusion_tag('math/formula_preview.html')
def formula_preview(text, max_formulas=3):
    if not text:
        return {'formulas': [], 'has_issues': False}

    processed = formula_processor.process_text_safe(text)
    all_formulas = processed.get('formulas', [])
    return {
        'formulas': all_formulas[:max_formulas],
        'total_count': len(all_formulas),
        'has_more': len(all_formulas) > max_formulas,
        'has_errors': processed.get('has_errors', False),
        'has_warnings': processed.get('has_warnings', False),
    }


@register.simple_tag
def math_status_alert(text, alert_id=None):
    if not formula_processor.has_math(text):
        return ''

    processed = formula_processor.process_text_safe(text)
    if not processed.get('has_errors') and not processed.get('has_warnings'):
        return ''

    alert_id = alert_id or 'math-alert'
    errors = processed.get('errors', [])
    warnings = processed.get('warnings', [])

    if errors:
        alert_class = 'alert-danger'
        icon = '🚨'
        title = 'Ошибки в формулах'
        items = errors
    elif warnings:
        alert_class = 'alert-warning'
        icon = '⚠️'
        title = 'Предупреждения в формулах'
        items = warnings
    else:
        return ''

    items_html = ''.join(f'<li>{escape(item)}</li>' for item in items)
    return mark_safe(
        f'<div class="alert {alert_class} alert-dismissible fade show" '
        f'role="alert" id="{alert_id}">'
        f'<h6>{icon} {title}</h6>'
        f'<ul class="mb-0">{items_html}</ul>'
        '<button type="button" class="btn-close" '
        'data-bs-dismiss="alert" aria-label="Закрыть"></button>'
        '</div>'
    )
