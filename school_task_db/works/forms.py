from django import forms
from django.forms import inlineformset_factory
from .models import Work, WorkAnalogGroup


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
        fields = ['analog_group', 'count', 'order', 'weight']
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
        }


WorkAnalogGroupFormSet = inlineformset_factory(
    Work, WorkAnalogGroup,
    form=WorkAnalogGroupForm,
    extra=0,
    can_delete=True,
)


class VariantGenerationForm(forms.Form):
    count = forms.IntegerField(
        label='Количество вариантов',
        min_value=1, max_value=50, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
