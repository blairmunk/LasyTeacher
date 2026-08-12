from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.functional import cached_property

from codifier.models import ContentEntry, Requirement
from curriculum.models import Topic, SubTopic
from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)
from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)
from tasks.models import Task, TaskImage, Source


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

    codifier_content_entries = forms.ModelMultipleChoiceField(
        label='Элементы содержания',
        queryset=ContentEntry.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 8,
        }),
    )
    codifier_requirements = forms.ModelMultipleChoiceField(
        label='Проверяемые требования',
        queryset=Requirement.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 8,
        }),
    )

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
        self._configure_codifier_fields()

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
            'codifier_content_entries', 'codifier_requirements',
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
            'content_element': forms.HiddenInput(),
            'requirement_element': forms.HiddenInput(),
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

    def _configure_codifier_fields(self):
        topic = self._selected_topic()
        current_content_ids = ()
        current_requirement_ids = ()
        if self.instance.pk:
            current_content_ids = tuple(
                self.instance.codifier_content_entries.values_list(
                    'pk',
                    flat=True,
                )
            )
            current_requirement_ids = tuple(
                self.instance.codifier_requirements.values_list(
                    'pk',
                    flat=True,
                )
            )
            self.initial['codifier_content_entries'] = current_content_ids
            self.initial['codifier_requirements'] = current_requirement_ids

        content_entries = ContentEntry.objects.all()
        requirements = Requirement.objects.all()
        if topic is not None:
            content_entries = content_entries.filter(
                codifier__subject=topic.subject,
            )
            requirements = requirements.filter(
                codifier__subject=topic.subject,
            )
        self.fields['codifier_content_entries'].queryset = (
            content_entries.filter(
                Q(codifier__is_active=True) | Q(pk__in=current_content_ids),
            ).select_related('codifier').order_by(
                '-codifier__year',
                'codifier__exam_type',
                'code',
            )
        )
        self.fields['codifier_requirements'].queryset = (
            requirements.filter(
                Q(codifier__is_active=True) | Q(pk__in=current_requirement_ids),
            ).select_related('codifier').order_by(
                '-codifier__year',
                'codifier__exam_type',
                'code',
            )
        )

    def _selected_topic(self):
        topic_id = self.data.get('topic') if self.is_bound else None
        if topic_id:
            try:
                return Topic.objects.filter(pk=topic_id).first()
            except (ValueError, ValidationError):
                return None
        if self.instance.pk:
            return self.instance.topic
        return None

    def clean(self):
        cleaned_data = super().clean()
        topic = cleaned_data.get('topic')
        subtopic = cleaned_data.get('subtopic')

        errors = validate_task_topic_selection(
            topic_id=str(topic.pk) if topic else '',
            subtopic_id=str(subtopic.pk) if subtopic else None,
            subtopic_topic_id=(
                str(subtopic.topic_id) if subtopic else None
            ),
        )
        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


class TaskImageForm(forms.ModelForm):
    @cached_property
    def image_display(self):
        return TaskImagePresentationService.build(self.instance)

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
