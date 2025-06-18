from django.contrib import admin
from .models import Task, TaskImage

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1
    fields = ['image', 'position', 'caption', 'order']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['get_display_id', 'text_preview', 'topic', 'task_type', 'difficulty', 'images_count', 'created_at']
    list_filter = ['task_type', 'difficulty', 'section', 'topic']
    search_fields = ['text', 'topic', 'section', 'uuid']  # Добавить поиск по UUID
    # filter_horizontal = ['analog_groups']
    readonly_fields = ['uuid', 'get_short_uuid', 'get_medium_uuid']
    
    def get_display_id(self, obj):
        return obj.get_display_id()
    get_display_id.short_description = 'ID'
    get_display_id.admin_order_field = 'uuid'
    
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
