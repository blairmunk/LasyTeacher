"""Django forms for document templates."""

import json

from django import forms

from core_logic.value_objects.document_type_catalog import get_document_type_catalog


class DocumentTemplateForm(forms.Form):
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
    template_type = forms.ChoiceField(
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
        required=False,
        widget=forms.HiddenInput,
    )
    is_default = forms.BooleanField(
        label='Использовать по умолчанию для этого типа',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, document_types=None, sections=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['template_type'].choices = [
            (item.document_type, item.title)
            for item in (document_types or get_document_type_catalog())
        ]
        self.fields['sections'].choices = [
            (
                item.section_type,
                f'{item.title} ({item.section_type})',
            )
            for item in (sections or [])
        ]

    def clean(self):
        cleaned_data = super().clean()
        selected_sections = cleaned_data.get('sections') or ()
        section_options = {}

        for section_type in selected_sections:
            raw_options = self.data.get(
                section_options_field_name(section_type),
                '',
            ).strip()
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

        cleaned_data['section_options'] = section_options
        return cleaned_data


def section_options_field_name(section_type):
    return f'section_options__{section_type}'
