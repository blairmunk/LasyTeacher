from django.contrib import admin

from core_logic.value_objects.review_session import (
    review_session_is_completed,
    review_session_progress_percentage,
)

from .models import ReviewSession, ReviewComment

@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'event', 'started_at', 'progress_percentage', 'is_completed']
    list_filter = ['started_at', 'finished_at', 'reviewer']
    search_fields = ['event__name', 'reviewer__username']
    readonly_fields = ['started_at']
    
    def progress_percentage(self, obj):
        progress = review_session_progress_percentage(
            total_participations=obj.total_participations,
            checked_participations=obj.checked_participations,
        )
        return f"{progress}%"
    progress_percentage.short_description = 'Прогресс'

    def is_completed(self, obj):
        return review_session_is_completed(obj.finished_at)
    is_completed.boolean = True
    is_completed.short_description = 'Завершена'

@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'category', 'usage_count', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['text']
    list_editable = ['is_active']
    
    def text_preview(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
    text_preview.short_description = 'Текст'
