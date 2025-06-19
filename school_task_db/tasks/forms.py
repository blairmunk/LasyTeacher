from django import forms
from .models import Task, TaskImage
from curriculum.models import Topic, SubTopic
from references.helpers import (
    get_task_type_choices,
    get_difficulty_choices, 
    get_cognitive_level_choices,
    get_content_elements_for_subject,
    get_requirement_elements_for_subject
)

class TaskForm(forms.ModelForm):
    """Форма создания/редактирования задания с динамическими справочниками"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Динамически загружаем choices из справочников
        self.fields['task_type'] = forms.ChoiceField(
            label='Тип задания',
            choices=get_task_type_choices(include_empty=True),
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        self.fields['difficulty'] = forms.ChoiceField(
            label='Сложность',
            choices=get_difficulty_choices(include_empty=True),
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        self.fields['cognitive_level'] = forms.ChoiceField(
            label='Когнитивный уровень',
            choices=get_cognitive_level_choices(include_empty=True),
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Настройка остальных полей
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
        
        # Поля кодификатора зависят от выбранной темы
        if self.instance.pk and self.instance.topic:
            subject = self.instance.topic.subject
            self.setup_codifier_fields(subject)
        
        # Подтемы зависят от выбранной темы
        if 'topic' in self.data or (self.instance.pk and self.instance.topic):
            try:
                topic_id = int(self.data.get('topic', self.instance.topic.pk))
                topic = Topic.objects.get(pk=topic_id)
                self.fields['subtopic'].queryset = topic.subtopics.all()
                
                # Обновляем поля кодификатора для выбранного предмета
                self.setup_codifier_fields(topic.subject)
            except (ValueError, TypeError, Topic.DoesNotExist):
                self.fields['subtopic'].queryset = SubTopic.objects.none()
        else:
            self.fields['subtopic'].queryset = SubTopic.objects.none()
    
    def setup_codifier_fields(self, subject):
        """Настройка полей кодификатора для конкретного предмета"""
        
        content_choices = get_content_elements_for_subject(subject, include_empty=True)
        requirement_choices = get_requirement_elements_for_subject(subject, include_empty=True)
        
        if content_choices and len(content_choices) > 1:  # Больше чем просто "Выберите"
            self.fields['content_element'] = forms.ChoiceField(
                label='Элемент содержания',
                choices=content_choices,
                required=False,
                widget=forms.Select(attrs={'class': 'form-select'})
            )
        
        if requirement_choices and len(requirement_choices) > 1:
            self.fields['requirement_element'] = forms.ChoiceField(
                label='Элемент требований',
                choices=requirement_choices,
                required=False,
                widget=forms.Select(attrs={'class': 'form-select'})
            )
    
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
            'topic': forms.Select(attrs={'class': 'form-select'}),
            'subtopic': forms.Select(attrs={'class': 'form-select'}),
            'short_solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'full_solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hint': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class TaskImageForm(forms.ModelForm):
    """Форма для загрузки изображений к заданию"""
    
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


# FormSet для работы с несколькими изображениями
TaskImageFormSet = modelformset_factory(
    TaskImage,
    form=TaskImageForm,
    extra=1,  # Одна пустая форма для добавления
    can_delete=True,  # Можно удалять изображения
    can_order=True   # Можно менять порядок
)
