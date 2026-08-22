from django.contrib import admin
from .models import Source
from django import forms
from django.core.exceptions import ValidationError
from .models import ImageAsset, Task, TaskImage
from infrastructure.forms.task_django_forms import TaskImageForm
from infrastructure.services.django_image_asset_store import (
    DjangoImageAssetStore,
)
from codifier.models import ContentEntry, Requirement
from curriculum.models import Topic, SubTopic
from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)
from infrastructure.services.django_task_classification_queries import (
    task_classification_querysets,
)

class TaskAdminForm(forms.ModelForm):
    """Кастомная форма для админки с фильтрацией подтем"""

    codifier_content_entries = forms.ModelMultipleChoiceField(
        label='Элементы содержания',
        queryset=ContentEntry.objects.none(),
        required=False,
    )
    codifier_requirements = forms.ModelMultipleChoiceField(
        label='Проверяемые требования',
        queryset=Requirement.objects.none(),
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            'text',
            'answer',
            'topic',
            'subtopic',
            'short_solution',
            'full_solution',
            'hint',
            'instruction',
            'task_type',
            'difficulty',
            'cognitive_level',
            'estimated_time',
            'codifier_content_entries',
            'codifier_requirements',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Тема обязательна
        self.fields['topic'].required = True
        
        # ИСПРАВЛЕНО: Всегда показываем ВСЕ подтемы для валидации
        self.fields['subtopic'].queryset = SubTopic.objects.all()
        
        # Подтема необязательна
        self.fields['subtopic'].required = False
        self.fields['subtopic'].empty_label = "--- Выберите подтему (необязательно) ---"
        self._configure_codifier_fields()

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

        content_entries, requirements = task_classification_querysets(
            topic=topic,
            current_content_ids=current_content_ids,
            current_requirement_ids=current_requirement_ids,
        )
        self.fields['codifier_content_entries'].queryset = content_entries
        self.fields['codifier_requirements'].queryset = requirements

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

    def _save_m2m(self):
        super()._save_m2m()
        self.instance.codifier_content_entries.set(
            self.cleaned_data.get('codifier_content_entries', ()),
        )
        self.instance.codifier_requirements.set(
            self.cleaned_data.get('codifier_requirements', ()),
        )
    
    def clean(self):
        """Валидация для админки"""
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

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = [
        'get_short_uuid',
        'short_name',
        'name',
        'source_type',
        'author',
        'year',
    ]
    list_filter = ['source_type', 'year']
    search_fields = ['name', 'short_name', 'author', 'isbn', '=id']
    readonly_fields = ['id']

    @admin.display(description='UUID')
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()

class TaskImageAdminForm(TaskImageForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get('image')
        if uploaded_file:
            instance.asset = DjangoImageAssetStore().get_or_create(
                uploaded_file,
            )
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class TaskImageInline(admin.TabularInline):
    model = TaskImage
    form = TaskImageAdminForm
    extra = 1
    fields = ['image', 'position', 'caption', 'order']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    
    list_display = ['get_short_uuid', 'text_preview', 'get_topic_name', 'task_type', 'get_difficulty_display', 'images_count', 'created_at']
    list_filter = ['task_type', 'difficulty', 'topic__subject', 'cognitive_level']
    search_fields = ['text', 'topic__name', 'topic__section', '=id']
    readonly_fields = ['id', 'get_short_uuid', 'get_medium_uuid']
    inlines = [TaskImageInline]
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['text', 'answer']
        }),
        ('Тематическая принадлежность', {
            'fields': ['topic', 'subtopic'],
            'description': '⚠️ Тема обязательна! Подтема необязательна.'
        }),
        ('Решения и подсказки', {
            'fields': ['short_solution', 'full_solution', 'hint', 'instruction'],
            'classes': ['collapse']
        }),
        ('Классификация', {
            'fields': ['task_type', 'difficulty', 'cognitive_level', 'estimated_time']
        }),
        ('Кодификатор', {
            'fields': [
                'codifier_content_entries',
                'codifier_requirements',
            ],
            'classes': ['collapse']
        }),
        ('Служебная информация', {
            'fields': ['id', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    class Media:
        js = ('admin/js/admin_inline.js',)
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def get_topic_name(self, obj):
        return obj.topic.name if obj.topic else 'Без темы'
    get_topic_name.short_description = 'Тема'
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Текст задания'
    
    def get_difficulty_display(self, obj):
        return obj.get_difficulty_display()
    get_difficulty_display.short_description = 'Сложность'
    
    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = 'Изображений'

@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    form = TaskImageAdminForm
    list_display = ['task', 'position', 'caption', 'order', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['task__text', 'caption']


@admin.register(ImageAsset)
class ImageAssetAdmin(admin.ModelAdmin):
    list_display = [
        'get_short_uuid',
        'original_filename',
        'mime_type',
        'byte_size',
        'checksum',
        'created_at',
    ]
    search_fields = ['=id', 'checksum', 'original_filename']
    readonly_fields = [
        'id',
        'file',
        'checksum',
        'byte_size',
        'mime_type',
        'original_filename',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='UUID')
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
