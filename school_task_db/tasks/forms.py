from django import forms
from django.forms import inlineformset_factory
from .models import Task, TaskImage

class TaskImageForm(forms.ModelForm):
    class Meta:
        model = TaskImage
        fields = ['image', 'position', 'caption', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Подпись к изображению (необязательно)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

# Формсет для изображений задания
TaskImageFormSet = inlineformset_factory(
    Task, TaskImage, form=TaskImageForm, extra=1, can_delete=True
)

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'text', 'answer', 'short_solution', 'full_solution', 'hint', 'instruction',
            'section', 'topic', 'subtopic', 'content_element', 'requirement_element',
            'task_type', 'difficulty'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
            'answer': forms.Textarea(attrs={'rows': 3}),
            'short_solution': forms.Textarea(attrs={'rows': 3}),
            'full_solution': forms.Textarea(attrs={'rows': 5}),
            'hint': forms.Textarea(attrs={'rows': 2}),
            'instruction': forms.Textarea(attrs={'rows': 2}),
        }
