from django.contrib import admin
from .models import Student, StudentGroup

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'middle_name', 'email', 'created_at']
    search_fields = ['last_name', 'first_name', 'email']
    list_filter = ['created_at']

@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'students_count', 'created_at']
    filter_horizontal = ['students']
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'Количество учеников'
