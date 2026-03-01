from django.contrib import admin
from .models import Work, WorkAnalogGroup, Variant, VariantTask


class WorkAnalogGroupInline(admin.TabularInline):
    model = WorkAnalogGroup
    extra = 1
    ordering = ['order']


class VariantTaskInline(admin.TabularInline):
    model = VariantTask
    extra = 0
    ordering = ['order']
    autocomplete_fields = ['task']
    readonly_fields = ['order']


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'work_type', 'duration', 'variant_counter', 'created_at']
    list_filter = ['work_type', 'duration', 'created_at']
    search_fields = ['name', 'uuid']
    readonly_fields = ['uuid', 'variant_counter']
    inlines = [WorkAnalogGroupInline]

    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'work', 'number', 'tasks_count', 'created_at']
    list_filter = ['work', 'work__work_type', 'created_at']
    search_fields = ['work__name', 'number', 'uuid']
    readonly_fields = ['uuid']
    inlines = [VariantTaskInline]

    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'

    def tasks_count(self, obj):
        return obj.tasks.count()
    tasks_count.short_description = 'Заданий'


@admin.register(WorkAnalogGroup)
class WorkAnalogGroupAdmin(admin.ModelAdmin):
    list_display = ['work', 'analog_group', 'count', 'order']
    list_filter = ['work', 'analog_group']
    search_fields = ['work__name', 'analog_group__name']
