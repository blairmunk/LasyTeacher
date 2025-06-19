from django.contrib import admin
from .models import Student, StudentGroup

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'last_name', 'first_name', 'middle_name', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['last_name', 'first_name', 'middle_name', 'email', 'uuid']
    readonly_fields = ['uuid', 'get_short_uuid']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['last_name', 'first_name', 'middle_name', 'email']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'

@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'get_students_count_safe', 'created_at']  # ИЗМЕНЕНО название метода
    search_fields = ['name', 'uuid']
    filter_horizontal = ['students']
    readonly_fields = ['uuid', 'get_short_uuid']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name']
        }),
        ('Ученики', {
            'fields': ['students']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def get_students_count_safe(self, obj):  # ПЕРЕИМЕНОВАННЫЙ МЕТОД для избежания конфликтов
        """Безопасное получение количества учеников"""
        try:
            return obj.get_students_count()
        except AttributeError:
            return obj.students.count()
    get_students_count_safe.short_description = 'Количество учеников'
    get_students_count_safe.admin_order_field = 'students'
