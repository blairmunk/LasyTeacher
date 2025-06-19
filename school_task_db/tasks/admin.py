from django.contrib import admin
from .models import Task, TaskImage

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1
    fields = ['image', 'position', 'caption', 'order']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'text_preview', 'get_topic_name', 'task_type', 'difficulty', 'images_count', 'created_at']
    list_filter = ['task_type', 'difficulty', 'topic__subject', 'topic__grade_level', 'cognitive_level']  # ОБНОВЛЕНО
    search_fields = ['text', 'topic__name', 'topic__section', 'uuid']  # ОБНОВЛЕНО: поиск через связь
    readonly_fields = ['uuid', 'get_short_uuid', 'get_medium_uuid']
    inlines = [TaskImageInline]
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['text', 'answer']
        }),
        ('Тематическая принадлежность', {
            'fields': ['topic', 'subtopic']  # ОБНОВЛЕНО
        }),
        ('Решения и подсказки', {
            'fields': ['short_solution', 'full_solution', 'hint', 'instruction'],
            'classes': ['collapse']
        }),
        ('Классификация', {
            'fields': ['task_type', 'difficulty', 'cognitive_level', 'estimated_time']  # ОБНОВЛЕНО
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
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    get_short_uuid.admin_order_field = 'uuid'
    
    def get_topic_name(self, obj):
        return obj.topic.name if obj.topic else 'Без темы'
    get_topic_name.short_description = 'Тема'
    get_topic_name.admin_order_field = 'topic__name'
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Текст задания'
    
    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = 'Изображений'

@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    list_display = ['task', 'position', 'caption', 'order', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['task__text', 'caption']
