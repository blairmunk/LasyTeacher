from django import forms
from django.forms import inlineformset_factory
from .models import Work, WorkAnalogGroup

class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = ['name', 'duration']

class WorkAnalogGroupForm(forms.ModelForm):
    class Meta:
        model = WorkAnalogGroup
        fields = ['analog_group', 'count']

# Формсет для групп аналогов в работе
WorkAnalogGroupFormSet = inlineformset_factory(
    Work, WorkAnalogGroup, form=WorkAnalogGroupForm, extra=1, can_delete=True
)

class VariantGenerationForm(forms.Form):
    count = forms.IntegerField(
        label='Количество вариантов',
        min_value=1,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
