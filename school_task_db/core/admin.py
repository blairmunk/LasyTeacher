from django.contrib import admin

from core_logic.services.import_log_service import ImportLogService
from core_logic.use_cases.activate_academic_year import (
    ActivateAcademicYearRequest,
)
from infrastructure.container import container

from .models import ImportLog, AcademicYear


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active']
    ordering = ['-start_date']

    def save_model(self, request, obj, form, change):
        should_activate = obj.is_active
        if should_activate:
            obj.is_active = False
        super().save_model(request, obj, form, change)
        if should_activate:
            active_year = container.activate_academic_year_use_case().execute(
                ActivateAcademicYearRequest(year_id=str(obj.pk)),
            )
            obj.is_active = bool(active_year and active_year.is_active)


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
        return (
            f'{ImportLogService.status_icon(obj.status)} '
            f'{obj.get_status_display()}'
        )
    status_icon_display.short_description = 'Статус'

    def duration_human(self, obj):
        return ImportLogService.duration_human(obj.duration_ms)
    duration_human.short_description = 'Время'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
