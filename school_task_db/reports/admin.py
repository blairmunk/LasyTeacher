from django.contrib import admin

from reports.models import EventReportNarrativeModel


@admin.register(EventReportNarrativeModel)
class EventReportNarrativeAdmin(admin.ModelAdmin):
    list_display = ['event', 'updated_at']
    search_fields = ['event__name']
    readonly_fields = ['created_at', 'updated_at']
