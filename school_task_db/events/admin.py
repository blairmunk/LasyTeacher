from django.contrib import admin
from .models import Event, EventParticipation, Mark

class EventParticipationInline(admin.TabularInline):
    """Inline для участников события"""
    model = EventParticipation
    extra = 1
    fields = ['student', 'variant', 'status', 'seat_number']
    # ВРЕМЕННО УБИРАЕМ autocomplete_fields до исправления всех админок
    autocomplete_fields = ['student', 'variant']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'work', 'planned_date', 'status', 'get_participants_count', 'get_progress']
    list_filter = ['status', 'planned_date', 'work__work_type', 'course']
    search_fields = ['name', 'work__name', 'uuid']  # ОБЯЗАТЕЛЬНО для автокомплита
    readonly_fields = ['uuid', 'get_short_uuid']
    inlines = [EventParticipationInline]
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'work', 'course']
        }),
        ('Временные параметры', {
            'fields': ['planned_date', 'actual_start', 'actual_end']
        }),
        ('Статус и описание', {
            'fields': ['status', 'description', 'location']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def get_participants_count(self, obj):
        return obj.get_participants_count()
    get_participants_count.short_description = 'Участников'
    
    def get_progress(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress.short_description = 'Прогресс'

@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'event', 'student', 'variant', 'status', 'completed_at']
    list_filter = ['status', 'event__work', 'completed_at']
    search_fields = ['event__name', 'student__last_name', 'student__first_name', 'uuid']  # ОБЯЗАТЕЛЬНО для автокомплита
    readonly_fields = ['uuid', 'get_short_uuid']
    # ВРЕМЕННО УБИРАЕМ autocomplete_fields
    autocomplete_fields = ['event', 'student', 'variant']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['event', 'student', 'variant']
        }),
        ('Статус и временные метки', {
            'fields': ['status', 'started_at', 'completed_at', 'graded_at']
        }),
        ('Дополнительно', {
            'fields': ['seat_number']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'get_student_name', 'get_event_name', 'score', 'points', 'get_percentage', 'checked_at']
    list_filter = ['score', 'checked_at', 'is_retake', 'is_excellent', 'needs_attention', 'participation__event__work']
    search_fields = ['participation__student__last_name', 'participation__student__first_name', 
                    'participation__event__name', 'teacher_comment', 'uuid']  # ОБЯЗАТЕЛЬНО для автокомплита
    readonly_fields = ['uuid', 'get_short_uuid', 'get_percentage']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['participation', 'score', 'points', 'max_points']
        }),
        ('Детализация', {
            'fields': ['task_scores', 'work_scan'],
            'classes': ['collapse']
        }),
        ('Комментарии', {
            'fields': ['teacher_comment', 'mistakes_analysis', 'recommendations'],
            'classes': ['collapse']
        }),
        ('Проверка', {
            'fields': ['checked_at', 'checked_by']
        }),
        ('Дополнительные метки', {
            'fields': ['is_retake', 'is_excellent', 'needs_attention']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()
    get_student_name.short_description = 'Ученик'
    get_student_name.admin_order_field = 'participation__student__last_name'
    
    def get_event_name(self, obj):
        return obj.event.name
    get_event_name.short_description = 'Событие'
    get_event_name.admin_order_field = 'participation__event__name'
    
    def get_percentage(self, obj):
        percentage = obj.get_percentage()
        return f"{percentage}%" if percentage else "—"
    get_percentage.short_description = '% выполнения'
