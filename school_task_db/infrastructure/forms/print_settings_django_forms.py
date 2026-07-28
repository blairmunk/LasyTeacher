"""Django forms for document print settings."""

import json

from django import forms

from core_logic.value_objects.document_recipes import (
    BLANK_CELLS_SECTION,
    TASK_LIST_SECTION,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
    DEFAULT_BLANK_CELLS_ROWS,
)


class PrintSettingsForm(forms.Form):
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
    sections = forms.MultipleChoiceField(
        label='Секции',
        choices=(),
        widget=forms.CheckboxSelectMultiple,
    )
    section_order = forms.CharField(
        label='Порядок секций',
        required=False,
        help_text=(
            'Коды секций через запятую. Повторяемые секции можно указать '
            'несколько раз.'
        ),
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 2,
                'spellcheck': 'false',
            },
        ),
    )
    custom_css = forms.CharField(
        label='Дополнительные стили CSS',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 5,
                'spellcheck': 'false',
            },
        ),
    )
    custom_latex_preamble = forms.CharField(
        label='Дополнительная LaTeX-преамбула',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 5,
                'spellcheck': 'false',
            },
        ),
    )
    html_template_override = forms.CharField(
        label='HTML-обёртка документа',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 7,
                'spellcheck': 'false',
            },
        ),
    )
    latex_template_override = forms.CharField(
        label='LaTeX-обёртка документа',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control font-monospace',
                'rows': 7,
                'spellcheck': 'false',
            },
        ),
    )
    blank_cells_rows = forms.IntegerField(
        label='Строки',
        required=False,
        min_value=1,
        max_value=40,
        initial=DEFAULT_BLANK_CELLS_ROWS,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    blank_cells_columns = forms.IntegerField(
        label='Столбцы',
        required=False,
        min_value=1,
        max_value=40,
        initial=DEFAULT_BLANK_CELLS_COLUMNS,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    blank_cells_row_height = forms.IntegerField(
        label='Высота строки, px',
        required=False,
        min_value=1,
        max_value=120,
        initial=DEFAULT_BLANK_CELLS_ROW_HEIGHT,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    task_list_theory_visible = forms.BooleanField(
        label='Теория',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    task_list_text_visible = forms.BooleanField(
        label='Текстовые блоки',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    is_default = forms.BooleanField(
        label='Использовать как оформление по умолчанию для этого типа',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, document_types=None, sections=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].choices = [
            (item.document_type, item.title)
            for item in (document_types or [])
        ]
        self.fields['sections'].choices = [
            (
                item.section_type,
                f'{item.title} ({item.section_type})',
            )
            for item in (sections or [])
        ]
        blank_cells_options = (
            self.initial.get('section_options', {})
            .get(BLANK_CELLS_SECTION, {})
        )
        self.initial.setdefault(
            'blank_cells_rows',
            blank_cells_options.get('rows', DEFAULT_BLANK_CELLS_ROWS),
        )
        self.initial.setdefault(
            'blank_cells_columns',
            blank_cells_options.get(
                'columns',
                DEFAULT_BLANK_CELLS_COLUMNS,
            ),
        )
        self.initial.setdefault(
            'blank_cells_row_height',
            blank_cells_options.get(
                'row_height',
                DEFAULT_BLANK_CELLS_ROW_HEIGHT,
            ),
        )
        task_list_options = (
            self.initial.get('section_options', {})
            .get(TASK_LIST_SECTION, {})
        )
        hidden_content_types = set(
            task_list_options.get('hidden_content_types') or (),
        )
        self.initial.setdefault(
            'task_list_theory_visible',
            'theory' not in hidden_content_types,
        )
        self.initial.setdefault(
            'task_list_text_visible',
            'text' not in hidden_content_types,
        )

    def clean(self):
        cleaned_data = super().clean()
        selected_sections = cleaned_data.get('sections') or ()
        section_options = {}
        touched_section_options = set()

        for section_type in selected_sections:
            field_name = section_options_field_name(section_type)
            if field_name in self.data:
                touched_section_options.add(section_type)
            raw_options = self.data.get(field_name, '').strip()
            if not raw_options:
                continue
            try:
                parsed_options = json.loads(raw_options)
            except json.JSONDecodeError as error:
                raise forms.ValidationError(
                    f'Настройки секции {section_type}: некорректный JSON.'
                ) from error
            if not isinstance(parsed_options, dict):
                raise forms.ValidationError(
                    f'Настройки секции {section_type} должны быть JSON-объектом.'
                )
            section_options[section_type] = parsed_options

        if BLANK_CELLS_SECTION in selected_sections:
            touched_section_options.add(BLANK_CELLS_SECTION)
            structured_options = {
                option_name: cleaned_data.get(field_name)
                for option_name, field_name in (
                    ('rows', 'blank_cells_rows'),
                    ('columns', 'blank_cells_columns'),
                    ('row_height', 'blank_cells_row_height'),
                )
                if cleaned_data.get(field_name) is not None
            }
            if structured_options:
                section_options[BLANK_CELLS_SECTION] = {
                    **section_options.get(BLANK_CELLS_SECTION, {}),
                    **structured_options,
                }

        if (
            TASK_LIST_SECTION in selected_sections
            and self.data.get('task_list_content_visibility_options') == '1'
        ):
            touched_section_options.add(TASK_LIST_SECTION)
            task_list_options = {}
            hidden_content_types = []
            if not cleaned_data.get('task_list_theory_visible'):
                hidden_content_types.append('theory')
            if not cleaned_data.get('task_list_text_visible'):
                hidden_content_types.append('text')
            if hidden_content_types:
                task_list_options['hidden_content_types'] = (
                    hidden_content_types
                )
            section_options[TASK_LIST_SECTION] = task_list_options

        cleaned_data['section_options'] = section_options
        cleaned_data['touched_section_options'] = frozenset(
            touched_section_options,
        )
        return cleaned_data

def section_options_field_name(section_type):
    return f'section_options__{section_type}'
