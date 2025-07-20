"""Template tags для рендеринга математических формул"""

from django import template
from django.utils.safestring import mark_safe
from latex_generator.utils.formula_utils import formula_processor

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
def math_count(text):
    """Возвращает количество формул в тексте"""
    return formula_processor.count_formulas(text)

@register.simple_tag
def math_indicator(text):
    """Показывает индикатор наличия формул"""
    if formula_processor.has_math(text):
        count = formula_processor.count_formulas(text)
        return mark_safe(f'<span class="badge bg-success formula-badge">📐 {count}</span>')
    return ''
