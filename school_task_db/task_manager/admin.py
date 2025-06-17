from django.contrib import admin
from .models import (
    Task, TaskImage, AnalogGroup, Work, WorkAnalogGroup, Variant,
    Student, StudentGroup, Event, Mark
)


class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1
    fields = ['image', 'position', 'caption', 'order']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'topic', 'task_type', 'difficulty', 'images_count', 'created_at']
    list_filter = ['task_type', 'difficulty', 'section', 'topic']
    search_fields = ['text', 'topic', 'section']
    filter_horizontal = ['analog_groups']
    inlines = [TaskImageInline]
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Текст задания'
    
    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = 'Изображений'


@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    list_display = ['task', 'position', 'caption', 'order', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['task__text', 'caption']


# Остальные admin классы остаются без изменений...
@admin.register(AnalogGroup)
class AnalogGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'tasks_count', 'created_at']
    search_fields = ['name', 'description']
    
    def tasks_count(self, obj):
        return obj.tasks.count()
    tasks_count.short_description = 'Количество заданий'


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


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'middle_name', 'email']
    search_fields = ['last_name', 'first_name', 'email']
    list_filter = ['created_at']


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'students_count', 'created_at']
    filter_horizontal = ['students']
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'Количество учеников'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'work', 'student_group', 'status']
    list_filter = ['status', 'date', 'work']
    search_fields = ['name']


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'variant', 'event', 'score', 'created_at']
    list_filter = ['score', 'event', 'created_at']
    search_fields = ['student__last_name', 'student__first_name']
    