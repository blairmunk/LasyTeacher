from django import forms
from .models import Task, TaskImage
from curriculum.models import Topic, SubTopic

class TaskForm(forms.ModelForm):
    """Форма создания/редактирования задания"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # НЕ ПЕРЕОПРЕДЕЛЯЕМ поля с choices - используем из модели!
        # Просто добавляем CSS классы
        self.fields['task_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['difficulty'].widget.attrs.update({'class': 'form-select'})
        self.fields['cognitive_level'].widget.attrs.update({'class': 'form-select'})
        
        # Настройка текстовых полей
        self.fields['text'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Введите текст задания...'
        })
        
        self.fields['answer'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Введите ответ...'
        })
        
        # Тема обязательна
        self.fields['topic'].widget.attrs.update({'class': 'form-select'})
        self.fields['topic'].required = True
        
        # ИСПРАВЛЕНО: Всегда показываем ВСЕ подтемы
        # Django нужен полный queryset для валидации!
        self.fields['subtopic'].queryset = SubTopic.objects.all()
        
        # Подтема необязательна
        self.fields['subtopic'].required = False
        self.fields['subtopic'].empty_label = "--- Выберите подтему (необязательно) ---"
        self.fields['subtopic'].widget.attrs.update({
            'data-depends-on': 'topic',
            'class': 'form-select'
        })
        
        # Делаем кодификатор необязательным
        self.fields['content_element'].required = False
        self.fields['requirement_element'].required = False
    
    class Meta:
        model = Task
        fields = [
            'text', 'answer', 'topic', 'subtopic',
            'task_type', 'difficulty', 'cognitive_level',
            'content_element', 'requirement_element',
            'short_solution', 'full_solution', 'hint', 'instruction',
            'estimated_time'
        ]
        widgets = {
            'short_solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'full_solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hint': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'content_element': forms.TextInput(attrs={'class': 'form-control'}),
            'requirement_element': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """Валидация с правильной проверкой подтем"""
        cleaned_data = super().clean()
        topic = cleaned_data.get('topic')
        subtopic = cleaned_data.get('subtopic')
        
        # Проверяем что тема выбрана
        if not topic:
            raise forms.ValidationError('Тема обязательна для выбора')
        
        # ГЛАВНАЯ ПРОВЕРКА: если подтема выбрана, она должна принадлежать теме
        if subtopic and topic and subtopic.topic != topic:
            raise forms.ValidationError('Выбранная подтема не принадлежит выбранной теме')
        
        return cleaned_data

# Остальные классы остаются без изменений
class TaskImageForm(forms.ModelForm):
    class Meta:
        model = TaskImage
        fields = ['image', 'position', 'caption', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

from django.forms import modelformset_factory

TaskImageFormSet = modelformset_factory(
    TaskImage,
    form=TaskImageForm,
    extra=1,
    can_delete=True,
    can_order=True
)
