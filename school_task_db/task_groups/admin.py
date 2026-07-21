from django.contrib import admin

from task_groups.models import AnalogGroup, TaskGroup


class TaskGroupInline(admin.TabularInline):
    model = TaskGroup
    extra = 0
    autocomplete_fields = ['task']


@admin.register(AnalogGroup)
class AnalogGroupAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'difficulty', 'created_at']
    list_filter = ['difficulty', 'created_at']
    search_fields = ['name', 'description', 'uuid']
    readonly_fields = ['uuid']
    inlines = [TaskGroupInline]

    def get_short_uuid(self, obj):
        return obj.get_short_uuid()

    get_short_uuid.short_description = 'UUID'


@admin.register(TaskGroup)
class TaskGroupAdmin(admin.ModelAdmin):
    list_display = ['task', 'group', 'bank_role', 'created_at']
    list_filter = ['bank_role', 'group']
    search_fields = ['task__text', 'group__name']
    autocomplete_fields = ['task', 'group']
