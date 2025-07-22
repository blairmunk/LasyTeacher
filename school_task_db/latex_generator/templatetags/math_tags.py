"""Template tags для рендеринга математических формул с обработкой ошибок"""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from document_generator.utils.formula_utils import formula_processor

register = template.Library()

@register.filter
def render_math(text):
    """Фильтр для рендеринга математических формул в веб-интерфейсе"""
    if not text:
        return ''
    
    # Для веб-рендеринга просто возвращаем текст как есть
    # MathJax обработает $ и $$ автоматически
    return mark_safe(text)

@register.filter  
def has_math(text):
    """Проверяет есть ли в тексте формулы"""
    return formula_processor.has_math(text)

@register.filter
def has_math_formulas(text):
    """Проверяет содержит ли текст математические формулы"""
    if not text:
        return False
    return formula_processor.has_math(text)

@register.filter  
def count_formulas(text):
    """Подсчитывает количество формул в тексте"""
    if not text:
        return 0
    return formula_processor.count_formulas(text)

@register.filter
def math_count(text):
    """Возвращает количество формул в тексте"""
    return formula_processor.count_formulas(text)

@register.filter
def math_errors(text):
    """НОВОЕ: Возвращает ошибки в формулах"""
    if not text:
        return []
    
    processed = formula_processor.process_text_safe(text)
    return processed.get('errors', [])

@register.filter
def math_warnings(text):
    """НОВОЕ: Возвращает предупреждения в формулах"""
    if not text:
        return []
    
    processed = formula_processor.process_text_safe(text)
    return processed.get('warnings', [])

@register.filter
def has_math_errors(text):
    """НОВОЕ: Проверяет есть ли ошибки в формулах"""
    if not text:
        return False
    
    processed = formula_processor.process_text_safe(text)
    return processed.get('has_errors', False)

@register.filter
def has_math_warnings(text):
    """НОВОЕ: Проверяет есть ли предупреждения в формулах"""
    if not text:
        return False
    
    processed = formula_processor.process_text_safe(text)
    return processed.get('has_warnings', False)

@register.simple_tag
def math_indicator(text):
    """Показывает индикатор наличия формул с индикацией ошибок"""
    if not formula_processor.has_math(text):
        return ''
    
    count = formula_processor.count_formulas(text)
    processed = formula_processor.process_text_safe(text)
    
    # Определяем стиль бейджа в зависимости от наличия ошибок
    if processed.get('has_errors', False):
        badge_class = 'bg-danger'
        icon = '⚠️'
        title = f"Формул: {count}. Есть ошибки!"
    elif processed.get('has_warnings', False):
        badge_class = 'bg-warning text-dark'
        icon = '⚡'
        title = f"Формул: {count}. Есть предупреждения"
    else:
        badge_class = 'bg-success'
        icon = '📐'
        title = f"Формул: {count}. Все корректно"
    
    return mark_safe(
        f'<span class="badge {badge_class} formula-badge" title="{title}">'
        f'{icon} {count}</span>'
    )

@register.inclusion_tag('math/formula_errors.html')
def show_formula_errors(text, show_warnings=True):
    """НОВОЕ: Показывает подробную информацию об ошибках формул"""
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
    """Показывает превью формул из текста с индикацией статуса"""
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
    """НОВОЕ: Генерирует alert с информацией о статусе формул"""
    if not formula_processor.has_math(text):
        return ''
    
    processed = formula_processor.process_text_safe(text)
    
    if not processed.get('has_errors') and not processed.get('has_warnings'):
        return ''  # Все хорошо, не показываем alert
    
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
    
    items_html = ''.join([f'<li>{escape(item)}</li>' for item in items])
    
    return mark_safe(f'''
    <div class="alert {alert_class} alert-dismissible fade show" role="alert" id="{alert_id}">
        <h6>{icon} {title}</h6>
        <ul class="mb-0">
            {items_html}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>
    </div>
    ''')
