from django import forms
from .models import AnalogGroup

class AnalogGroupForm(forms.ModelForm):
    class Meta:
        model = AnalogGroup
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
