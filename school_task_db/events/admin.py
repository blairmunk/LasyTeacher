from django.contrib import admin
from .models import Event, Mark

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'work', 'student_group', 'status', 'created_at']
    list_filter = ['status', 'date', 'work']
    search_fields = ['name']

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'variant', 'event', 'score', 'created_at']
    list_filter = ['score', 'event', 'created_at']
    search_fields = ['student__last_name', 'student__first_name']
