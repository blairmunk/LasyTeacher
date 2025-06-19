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
            'topic', 'subtopic', 'content_element', 'requirement_element',  # ОБНОВЛЕНО: убрали section, topic стал связью
            'task_type', 'difficulty', 'cognitive_level', 'estimated_time'  # ДОБАВЛЕНО: новые поля
        ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
            'answer': forms.Textarea(attrs={'rows': 3}),
            'short_solution': forms.Textarea(attrs={'rows': 3}),
            'full_solution': forms.Textarea(attrs={'rows': 5}),
            'hint': forms.Textarea(attrs={'rows': 2}),
            'instruction': forms.Textarea(attrs={'rows': 2}),
            'topic': forms.Select(attrs={'class': 'form-select'}),  # НОВОЕ: связь с Topic
            'subtopic': forms.Select(attrs={'class': 'form-select'}),  # НОВОЕ: связь с Topic
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'cognitive_level': forms.Select(attrs={'class': 'form-select'}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настраиваем queryset для подтем в зависимости от выбранной темы
        if 'topic' in self.data:
            try:
                topic_id = int(self.data.get('topic'))
                from curriculum.models import Topic
                self.fields['subtopic'].queryset = Topic.objects.filter(parent_id=topic_id)
            except (ValueError, TypeError):
                self.fields['subtopic'].queryset = Topic.objects.none()
        elif self.instance.pk and self.instance.topic:
            self.fields['subtopic'].queryset = self.instance.topic.subtopics.all()
        else:
            self.fields['subtopic'].queryset = Topic.objects.none()
