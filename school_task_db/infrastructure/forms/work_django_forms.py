from django import forms
from django.forms import inlineformset_factory

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_RENDER_MODE_TASK_ONLY,
)
from works.models import Work, WorkAnalogGroup, WorkContentBlock
from core_logic.value_objects.work_assessment import WORK_ASSESSMENT_MODE_VARIANT


class WorkForm(forms.ModelForm):
    assessment_mode = forms.ChoiceField(
        label='Проверка работы',
        choices=Work._meta.get_field('assessment_mode').choices,
        help_text=(
            'Для распечатанного материала вне базы выберите итоговую оценку: '
            'варианты и задания назначать не потребуется.'
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    def clean_assessment_mode(self):
        return self.cleaned_data.get(
            'assessment_mode',
        ) or WORK_ASSESSMENT_MODE_VARIANT

    class Meta:
        model = Work
        fields = [
            'name',
            'work_type',
            'assessment_mode',
            'duration',
            'max_score',
        ]
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
                'class': 'form-control order-field',
                'min': 0,
                'style': 'width: 80px',
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


class WorkContentBlockForm(forms.ModelForm):
    class Meta:
        model = WorkContentBlock
        fields = [
            'content_type',
            'order',
            'title',
            'body',
            'topics',
            'include_subtopics',
        ]
        widgets = {
            'content_type': forms.Select(
                attrs={'class': 'form-select content-type-field'},
            ),
            'order': forms.NumberInput(
                attrs={
                    'class': 'form-control content-order-field',
                    'min': 0,
                },
            ),
            'title': forms.TextInput(
                attrs={'class': 'form-control'},
            ),
            'body': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3},
            ),
            'topics': forms.SelectMultiple(
                attrs={
                    'class': 'form-select',
                    'size': 5,
                },
            ),
            'include_subtopics': forms.CheckboxInput(
                attrs={'class': 'form-check-input'},
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        if (
            content_type == 'theory'
            and not cleaned_data.get('topics')
        ):
            self.add_error(
                'topics',
                'Выберите хотя бы одну тему.',
            )
        if (
            content_type == 'text'
            and not (cleaned_data.get('body') or '').strip()
        ):
            self.add_error(
                'body',
                'Введите текст блока.',
            )
        return cleaned_data


WorkContentBlockFormSet = inlineformset_factory(
    Work,
    WorkContentBlock,
    form=WorkContentBlockForm,
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
