from django import forms
from .models import Student, StudentGroup

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'middle_name', 'email']

class StudentGroupForm(forms.ModelForm):
    class Meta:
        model = StudentGroup
        fields = ['name', 'students']
        widgets = {
            'students': forms.CheckboxSelectMultiple(),
        }
