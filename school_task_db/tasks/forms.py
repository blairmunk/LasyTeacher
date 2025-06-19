from django import forms
from django.forms import inlineformset_factory
from .models import Task, TaskImage
from curriculum.models import SubTopic  # ДОБАВИТЬ ИМПОРТ В НАЧАЛО

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

TaskImageFormSet = inlineformset_factory(
    Task, TaskImage, form=TaskImageForm, extra=1, can_delete=True
)

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'text', 'answer', 'short_solution', 'full_solution', 'hint', 'instruction',
            'topic', 'subtopic', 'content_element', 'requirement_element',
            'task_type', 'difficulty', 'cognitive_level', 'estimated_time'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'short_solution': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'full_solution': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'hint': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'instruction': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'topic': forms.Select(attrs={'class': 'form-select', 'id': 'id_topic'}),
            'subtopic': forms.Select(attrs={'class': 'form-select', 'id': 'id_subtopic'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'cognitive_level': forms.Select(attrs={'class': 'form-select'}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ограничиваем подтемы только теми, что принадлежат выбранной теме
        if 'topic' in self.data:
            try:
                topic_id = int(self.data.get('topic'))
                # УБРАТЬ локальный импорт
                self.fields['subtopic'].queryset = SubTopic.objects.filter(topic_id=topic_id).order_by('order')
            except (ValueError, TypeError):
                self.fields['subtopic'].queryset = SubTopic.objects.none()
        elif self.instance.pk and self.instance.topic:
            self.fields['subtopic'].queryset = self.instance.topic.subtopics.all().order_by('order')
        else:
            self.fields['subtopic'].queryset = SubTopic.objects.none()
            
        # Добавляем пустой вариант для подтем
        self.fields['subtopic'].empty_label = "--- Выберите подтему (необязательно) ---"
