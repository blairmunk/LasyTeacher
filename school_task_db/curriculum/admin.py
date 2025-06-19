from django.contrib import admin
from .models import Topic, SubTopic, Course, CourseAssignment

class SubTopicInline(admin.TabularInline):
    model = SubTopic
    extra = 1
    fields = ['name', 'description', 'order']

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'subject', 'grade_level', 'section', 'subtopics_count', 'order']
    list_filter = ['subject', 'grade_level', 'difficulty_level']
    search_fields = ['name', 'section', 'description']
    list_editable = ['order']
    readonly_fields = ['uuid', 'get_short_uuid']
    inlines = [SubTopicInline]
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'description']
        }),
        ('Классификация', {
            'fields': ['subject', 'grade_level', 'section', 'difficulty_level', 'order']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def subtopics_count(self, obj):
        return obj.get_subtopics_count()
    subtopics_count.short_description = 'Подтем'

@admin.register(SubTopic)
class SubTopicAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'topic', 'order']
    list_filter = ['topic__subject', 'topic__grade_level', 'topic__section']
    search_fields = ['name', 'description', 'topic__name']
    list_editable = ['order']
    readonly_fields = ['uuid', 'get_short_uuid']
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'

# Остальные админки остаются без изменений
class CourseAssignmentInline(admin.TabularInline):
    model = CourseAssignment
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'subject', 'grade_level', 'academic_year', 'is_active']
    list_filter = ['subject', 'grade_level', 'academic_year', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['uuid']
    inlines = [CourseAssignmentInline]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
