from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'school_name', 'teacher_name', 'default_subject',
            'current_academic_year', 'points_scale',
            'default_variants_count', 'logo',
            'pdf_font_size', 'pdf_margin_top', 'pdf_margin_bottom',
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'teacher_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_subject': forms.TextInput(attrs={'class': 'form-control'}),
            'current_academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'points_scale': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'default_variants_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'pdf_font_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 8, 'max': 16}),
            'pdf_margin_top': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 40}),
            'pdf_margin_bottom': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 40}),
        }
