from django.contrib import admin

from .models import PresentationProfile


@admin.register(PresentationProfile)
class PresentationProfileAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'document_type',
        'is_default',
        'is_public',
        'created_by',
        'updated_at',
    ]
    list_filter = ['document_type', 'is_default', 'is_public']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = [
        ('Основная информация', {
            'fields': [
                'name',
                'description',
                'document_type',
                'created_by',
                'is_default',
                'is_public',
            ],
        }),
        ('Шаблоны оформления', {
            'fields': [
                'latex_template_override',
                'html_template_override',
                'custom_css',
                'custom_latex_preamble',
            ],
            'classes': ['collapse'],
        }),
        ('Служебная информация', {
            'fields': ['id', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
