from django.contrib import admin
from .models import ReviewSession, ReviewComment

@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'event', 'started_at', 'progress_percentage', 'is_completed']
    list_filter = ['started_at', 'finished_at', 'reviewer']
    search_fields = ['event__name', 'reviewer__username']
    readonly_fields = ['started_at']
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = 'Прогресс'

@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'category', 'usage_count', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['text']
    list_editable = ['is_active']
    
    def text_preview(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
    text_preview.short_description = 'Текст'
