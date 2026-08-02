"""Django forms for document presentation profiles."""

from django import forms

from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    STUDENT_DIGEST_DOCUMENT_TYPE,
)


HTML_ONLY_DOCUMENT_TYPES = {
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    STUDENT_DIGEST_DOCUMENT_TYPE,
}


class PresentationProfileForm(forms.Form):
    name = forms.CharField(
        label='Название',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    description = forms.CharField(
        label='Описание',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
    document_type = forms.ChoiceField(
        label='Тип документа',
        choices=(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    custom_css = forms.CharField(
        label='CSS для HTML и PDF',
        required=False,
        help_text=(
            'Добавляется в HTML-документ после базовых стилей. '
            'PDF через Playwright использует тот же CSS.'
        ),
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 9,
                'spellcheck': 'false',
                'placeholder': (
                    '.document-section { margin-bottom: 1.5rem; }\n'
                    '.document-theory-block { padding: 1rem; }'
                ),
            },
        ),
    )
    custom_latex_preamble = forms.CharField(
        label='Дополнительная LaTeX-преамбула',
        required=False,
        help_text=(
            'Вставляется после стандартных пакетов и определений окружений, '
            'до начала документа.'
        ),
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 9,
                'spellcheck': 'false',
                'placeholder': (
                    '\\usepackage{xcolor}\n'
                    '\\renewenvironment{schooltheory}'
                    '{\\small\\color{gray}}{}'
                ),
            },
        ),
    )
    html_template_override = forms.CharField(
        label='Полная HTML-обёртка',
        required=False,
        help_text='Должна содержать {{ body_content|safe }}.',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 8,
                'spellcheck': 'false',
                'placeholder': (
                    '<!doctype html>\n<html lang="ru">\n'
                    '<body>\n{{ body_content|safe }}\n</body>\n</html>'
                ),
            },
        ),
    )
    latex_template_override = forms.CharField(
        label='Полная LaTeX-обёртка',
        required=False,
        help_text='Должна содержать {{ body_content|safe }}.',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 8,
                'spellcheck': 'false',
                'placeholder': (
                    '\\documentclass{article}\n'
                    '\\begin{document}\n'
                    '{{ body_content|safe }}\n'
                    '\\end{document}'
                ),
            },
        ),
    )
    is_default = forms.BooleanField(
        label='Предлагать этот профиль при печати данного типа документа',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, document_types=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].choices = [
            (item.document_type, item.title)
            for item in (document_types or [])
        ]

    def clean_html_template_override(self):
        return self._clean_wrapper('html_template_override', 'HTML')

    def clean_latex_template_override(self):
        if self.cleaned_data.get('document_type') in HTML_ONLY_DOCUMENT_TYPES:
            return ''
        return self._clean_wrapper('latex_template_override', 'LaTeX')

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('document_type') in HTML_ONLY_DOCUMENT_TYPES:
            cleaned_data['custom_latex_preamble'] = ''
            cleaned_data['latex_template_override'] = ''
        return cleaned_data

    def _clean_wrapper(self, field_name, label):
        value = self.cleaned_data.get(field_name, '')
        if value and '{{ body_content' not in value:
            raise forms.ValidationError(
                f'{label}-обёртка должна содержать {{{{ body_content|safe }}}}.',
            )
        return value
