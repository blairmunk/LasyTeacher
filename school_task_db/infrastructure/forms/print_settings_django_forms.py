"""Django forms for document print settings."""

import json

from django import forms

from core_logic.value_objects.document_recipes import (
    BLANK_CELLS_SECTION,
    TASK_LIST_SECTION,
    THEORY_SECTION,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_SPECIFIC_CHOICES,
    TASK_RENDER_MODE_CHOICES,
)

TASK_LIST_BLANK_CELLS_DEFAULT = ''
TASK_LIST_BLANK_CELLS_SHOW = 'show'
TASK_LIST_BLANK_CELLS_HIDE = 'hide'
TASK_LIST_BLANK_CELLS_MODE_CHOICES = (
    (TASK_LIST_BLANK_CELLS_DEFAULT, 'По спецификации'),
    (TASK_LIST_BLANK_CELLS_SHOW, 'Показывать'),
    (TASK_LIST_BLANK_CELLS_HIDE, 'Скрывать'),
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
    theory_section_title = forms.CharField(
        label='Заголовок блока',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    theory_include_subtopics = forms.BooleanField(
        label='Добавлять описания подтем',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    is_default = forms.BooleanField(
        label='Использовать по умолчанию для этого типа',
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
        self._add_task_list_role_fields()
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
        theory_options = (
            self.initial.get('section_options', {})
            .get(THEORY_SECTION, {})
        )
        self.initial.setdefault(
            'theory_section_title',
            theory_options.get('section_title', ''),
        )
        self.initial.setdefault(
            'theory_include_subtopics',
            theory_options.get('include_subtopics', False),
        )

    def _add_task_list_role_fields(self):
        task_list_options = (
            self.initial.get('section_options', {})
            .get(TASK_LIST_SECTION, {})
        )
        hidden_roles = set(task_list_options.get('hidden_roles') or ())
        render_modes = dict(
            task_list_options.get('role_render_modes') or {}
        )
        blank_cells = dict(
            task_list_options.get('role_blank_cells') or {}
        )
        for role, label in TASK_BANK_ROLE_SPECIFIC_CHOICES:
            self.fields[task_list_role_field_name(role, 'visible')] = (
                forms.BooleanField(
                    label='Показывать',
                    required=False,
                    initial=role not in hidden_roles,
                )
            )
            self.fields[task_list_role_field_name(role, 'render_mode')] = (
                forms.ChoiceField(
                    label='Содержимое',
                    required=False,
                    choices=(('', 'По спецификации'), *TASK_RENDER_MODE_CHOICES),
                    initial=render_modes.get(role, ''),
                )
            )
            blank_cells_mode, blank_cells_rows = (
                _blank_cells_role_initial(blank_cells.get(role))
                if role in blank_cells
                else (TASK_LIST_BLANK_CELLS_DEFAULT, DEFAULT_BLANK_CELLS_ROWS)
            )
            self.fields[
                task_list_role_field_name(role, 'blank_cells_mode')
            ] = forms.ChoiceField(
                label='Клетки',
                required=False,
                choices=TASK_LIST_BLANK_CELLS_MODE_CHOICES,
                initial=blank_cells_mode,
            )
            self.fields[
                task_list_role_field_name(role, 'blank_cells_rows')
            ] = forms.IntegerField(
                label='Строки',
                required=False,
                min_value=1,
                max_value=40,
                initial=blank_cells_rows,
            )
            for suffix in (
                'visible',
                'render_mode',
                'blank_cells_mode',
                'blank_cells_rows',
            ):
                self.fields[
                    task_list_role_field_name(role, suffix)
                ].widget.attrs['class'] = (
                    'form-check-input'
                    if suffix == 'visible'
                    else 'form-select'
                    if suffix in ('render_mode', 'blank_cells_mode')
                    else 'form-control'
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
            and self.data.get('task_list_structured_options') == '1'
        ):
            touched_section_options.add(TASK_LIST_SECTION)
            section_options[TASK_LIST_SECTION] = (
                self._clean_task_list_role_options(cleaned_data)
            )

        if (
            THEORY_SECTION in selected_sections
            and self.data.get('theory_structured_options') == '1'
        ):
            touched_section_options.add(THEORY_SECTION)
            theory_options = {}
            section_title = cleaned_data.get('theory_section_title', '').strip()
            if section_title:
                theory_options['section_title'] = section_title
            if cleaned_data.get('theory_include_subtopics'):
                theory_options['include_subtopics'] = True
            section_options[THEORY_SECTION] = theory_options

        cleaned_data['section_options'] = section_options
        cleaned_data['touched_section_options'] = frozenset(
            touched_section_options,
        )
        return cleaned_data

    def _clean_task_list_role_options(self, cleaned_data):
        hidden_roles = []
        render_modes = {}
        blank_cells = {}
        for role, _label in TASK_BANK_ROLE_SPECIFIC_CHOICES:
            if not cleaned_data.get(
                task_list_role_field_name(role, 'visible'),
            ):
                hidden_roles.append(role)

            render_mode = cleaned_data.get(
                task_list_role_field_name(role, 'render_mode'),
            )
            if render_mode:
                render_modes[role] = render_mode

            blank_cells_mode = cleaned_data.get(
                task_list_role_field_name(role, 'blank_cells_mode'),
            )
            if blank_cells_mode == TASK_LIST_BLANK_CELLS_HIDE:
                blank_cells[role] = False
            elif blank_cells_mode == TASK_LIST_BLANK_CELLS_SHOW:
                blank_cells[role] = {
                    'rows': (
                        cleaned_data.get(
                            task_list_role_field_name(
                                role,
                                'blank_cells_rows',
                            ),
                        )
                        or DEFAULT_BLANK_CELLS_ROWS
                    ),
                }

        options = {}
        if hidden_roles:
            options['hidden_roles'] = hidden_roles
        if render_modes:
            options['role_render_modes'] = render_modes
        if blank_cells:
            options['role_blank_cells'] = blank_cells
        return options


def section_options_field_name(section_type):
    return f'section_options__{section_type}'


def task_list_role_field_name(role, suffix):
    return f'task_list_{role}_{suffix}'


def _blank_cells_role_initial(value):
    if value is False or value is None:
        return TASK_LIST_BLANK_CELLS_HIDE, DEFAULT_BLANK_CELLS_ROWS
    if value is True:
        return TASK_LIST_BLANK_CELLS_SHOW, DEFAULT_BLANK_CELLS_ROWS
    if isinstance(value, int):
        return TASK_LIST_BLANK_CELLS_SHOW, value
    if not isinstance(value, dict):
        return TASK_LIST_BLANK_CELLS_DEFAULT, DEFAULT_BLANK_CELLS_ROWS
    if value.get('enabled', True) is False:
        return TASK_LIST_BLANK_CELLS_HIDE, DEFAULT_BLANK_CELLS_ROWS
    return (
        TASK_LIST_BLANK_CELLS_SHOW,
        value.get('rows', DEFAULT_BLANK_CELLS_ROWS),
    )
