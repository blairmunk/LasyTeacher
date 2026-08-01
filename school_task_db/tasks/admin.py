from django.contrib import admin
from .models import Source
from django import forms
from .models import Task, TaskImage
from curriculum.models import Topic, SubTopic
from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)

class TaskAdminForm(forms.ModelForm):
    """Кастомная форма для админки с фильтрацией подтем"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Тема обязательна
        self.fields['topic'].required = True
        
        # ИСПРАВЛЕНО: Всегда показываем ВСЕ подтемы для валидации
        self.fields['subtopic'].queryset = SubTopic.objects.all()
        
        # Подтема необязательна
        self.fields['subtopic'].required = False
        self.fields['subtopic'].empty_label = "--- Выберите подтему (необязательно) ---"
    
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
    list_display = ['short_name', 'name', 'source_type', 'author', 'year']
    list_filter = ['source_type', 'year']
    search_fields = ['name', 'short_name', 'author']

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1
    fields = ['image', 'position', 'caption', 'order']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    
    list_display = ['get_short_uuid', 'text_preview', 'get_topic_name', 'task_type', 'get_difficulty_display', 'images_count', 'created_at']
    list_filter = ['task_type', 'difficulty', 'topic__subject', 'cognitive_level']
    search_fields = ['text', 'topic__name', 'topic__section', 'uuid']
    readonly_fields = ['uuid', 'get_short_uuid', 'get_medium_uuid']
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
            'fields': ['content_element', 'requirement_element'],
            'classes': ['collapse']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
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
    list_display = ['task', 'position', 'caption', 'order', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['task__text', 'caption']
