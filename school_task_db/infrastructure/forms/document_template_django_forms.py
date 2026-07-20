"""Django forms for document templates."""

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
