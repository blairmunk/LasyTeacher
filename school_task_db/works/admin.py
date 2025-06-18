from django.contrib import admin
from .models import Work, WorkAnalogGroup, Variant

class WorkAnalogGroupInline(admin.TabularInline):
    model = WorkAnalogGroup
    extra = 1

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'variant_counter', 'created_at']
    search_fields = ['name']
    inlines = [WorkAnalogGroupInline]

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ['work', 'number', 'tasks_count', 'created_at']
    list_filter = ['work']
    filter_horizontal = ['tasks']
    
    def tasks_count(self, obj):
        return obj.tasks.count()
    tasks_count.short_description = 'Количество заданий'

@admin.register(WorkAnalogGroup)
class WorkAnalogGroupAdmin(admin.ModelAdmin):
    list_display = ['work', 'analog_group', 'count', 'created_at']
    list_filter = ['work', 'analog_group']
