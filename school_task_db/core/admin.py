from django.contrib import admin
from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'status_icon_display', 'filename', 'mode', 'dry_run',
        'tasks_created', 'tasks_updated', 'errors_count',
        'duration_human', 'created_at',
    ]
    list_filter = ['status', 'mode', 'dry_run', 'created_at']
    readonly_fields = [
        'id', 'filename', 'mode', 'dry_run', 'status',
        'tasks_created', 'tasks_updated', 'tasks_skipped',
        'groups_created', 'topics_created', 'images_created',
        'errors_count', 'details', 'error_messages',
        'file_size', 'duration_ms', 'created_at', 'updated_at',
    ]
    ordering = ['-created_at']
    
    def status_icon_display(self, obj):
        return f'{obj.status_icon} {obj.get_status_display()}'
    status_icon_display.short_description = 'Статус'
    
    def duration_human(self, obj):
        return obj.duration_human
    duration_human.short_description = 'Время'
    
    def has_add_permission(self, request):
        return False  # Логи создаются только программно
    
    def has_change_permission(self, request, obj=None):
        return False  # Логи нельзя редактировать
