from django import forms
from .models import Task, TaskImage, Source
from curriculum.models import Topic, SubTopic


class SourceForm(forms.ModelForm):
    """Форма создания источника"""
    class Meta:
        model = Source
        fields = ['name', 'short_name', 'source_type', 'author', 'year', 'url', 'isbn', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'Напр.: Перышкин-8'}),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2030}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TaskForm(forms.ModelForm):
    """Форма создания/редактирования задания"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # CSS классы для select-полей
        self.fields['task_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['difficulty'].widget.attrs.update({'class': 'form-select'})
        self.fields['cognitive_level'].widget.attrs.update({'class': 'form-select'})

        # Текстовые поля
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

        # Подтемы
        self.fields['subtopic'].queryset = SubTopic.objects.all()
        self.fields['subtopic'].required = False
        self.fields['subtopic'].empty_label = "--- Выберите подтему (необязательно) ---"
        self.fields['subtopic'].widget.attrs.update({
            'data-depends-on': 'topic',
            'class': 'form-select'
        })

        # Кодификатор необязателен
        self.fields['content_element'].required = False
        self.fields['requirement_element'].required = False

        # === Новые поля ===
        self.fields['source'].required = False
        self.fields['source'].empty_label = "--- Без источника ---"
        self.fields['source'].widget.attrs.update({'class': 'form-select'})

        self.fields['source_detail'].required = False
        self.fields['grade'].required = False
        self.fields['year'].required = False
        self.fields['teacher_notes'].required = False
        self.fields['is_verified'].required = False

    class Meta:
        model = Task
        fields = [
            'text', 'answer', 'topic', 'subtopic',
            'task_type', 'difficulty', 'cognitive_level',
            'content_element', 'requirement_element',
            'short_solution', 'full_solution', 'hint', 'instruction',
            'estimated_time',
            # Новые поля
            'source', 'source_detail', 'grade', 'year',
            'is_verified', 'teacher_notes',
        ]
        widgets = {
            'short_solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'full_solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hint': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'content_element': forms.TextInput(attrs={'class': 'form-control'}),
            'requirement_element': forms.TextInput(attrs={'class': 'form-control'}),
            # Новые виджеты
            'source_detail': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Стр. 45, №12 / Вариант 3, задание 5'
            }),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 2000, 'max': 2030,
                'placeholder': '2024'
            }),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'teacher_notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Личные пометки, типичные ошибки учеников...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        topic = cleaned_data.get('topic')
        subtopic = cleaned_data.get('subtopic')

        if not topic:
            raise forms.ValidationError('Тема обязательна для выбора')

        if subtopic and topic and subtopic.topic != topic:
            raise forms.ValidationError('Выбранная подтема не принадлежит выбранной теме')

        return cleaned_data


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


from django.forms import inlineformset_factory

TaskImageFormSet = inlineformset_factory(
    Task, TaskImage,
    form=TaskImageForm,
    extra=2,
    can_delete=True,
    max_num=10,
    validate_max=True,
    can_order=False
)
