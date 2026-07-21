from django import forms
from django.forms import inlineformset_factory

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_RENDER_MODE_TASK_ONLY,
)
from works.models import Work, WorkAnalogGroup


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = ['name', 'work_type', 'duration', 'max_score']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'work_type': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0,
                'placeholder': '0 = сумма весов',
            }),
        }


class WorkAnalogGroupForm(forms.ModelForm):
    class Meta:
        model = WorkAnalogGroup
        fields = [
            'analog_group',
            'count',
            'order',
            'weight',
            'bank_role_filter',
            'render_mode',
            'is_assessable',
            'blank_cells_after',
            'blank_cells_rows',
        ]
        widgets = {
            'analog_group': forms.Select(attrs={'class': 'form-select'}),
            'count': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'style': 'width: 80px',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'style': 'width: 80px',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'style': 'width: 70px',
            }),
            'bank_role_filter': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'render_mode': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'is_assessable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blank_cells_after': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blank_cells_rows': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': 1,
                'max': 40,
                'style': 'width: 80px',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_role_filter'].required = False
        self.fields['render_mode'].required = False
        self.fields['blank_cells_rows'].required = False
        self.fields['is_assessable'].initial = True

    def clean_bank_role_filter(self):
        return self.cleaned_data['bank_role_filter'] or TASK_BANK_ROLE_ANY

    def clean_render_mode(self):
        return self.cleaned_data['render_mode'] or TASK_RENDER_MODE_TASK_ONLY

    def clean_blank_cells_rows(self):
        return self.cleaned_data['blank_cells_rows'] or DEFAULT_BLANK_CELLS_ROWS


WorkAnalogGroupFormSet = inlineformset_factory(
    Work,
    WorkAnalogGroup,
    form=WorkAnalogGroupForm,
    extra=0,
    can_delete=True,
)


class VariantGenerationForm(forms.Form):
    count = forms.IntegerField(
        label='Количество вариантов',
        min_value=1,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
