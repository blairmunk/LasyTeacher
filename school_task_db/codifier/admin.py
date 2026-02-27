from django.contrib import admin
from .models import CodifierSpec, ContentEntry, Requirement


class ContentEntryInline(admin.TabularInline):
    model = ContentEntry
    extra = 0
    fields = ['code', 'name', 'parent', 'topic', 'subtopic', 'grade_studied']
    autocomplete_fields = ['topic', 'subtopic', 'parent']
    show_change_link = True



class RequirementInline(admin.TabularInline):
    model = Requirement
    extra = 0
    fields = ['code', 'name', 'cognitive_level']


@admin.register(CodifierSpec)
class CodifierSpecAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'exam_type', 'year', 'subject', 'is_active']
    list_filter = ['exam_type', 'year', 'is_active']
    search_fields = ['name', 'short_name']
    inlines = [ContentEntryInline, RequirementInline]


@admin.register(ContentEntry)
class ContentEntryAdmin(admin.ModelAdmin):
    list_display = ['code', 'short_name', 'codifier', 'parent_code',
                    'topic', 'subtopic', 'task_count', 'grade_studied']
    list_filter = ['codifier', 'codifier__exam_type']
    search_fields = ['code', 'name']
    autocomplete_fields = ['topic', 'subtopic', 'parent', 'codifier']
    list_editable = ['topic', 'subtopic']
    list_per_page = 50

    def short_name(self, obj):
        return obj.name[:80]
    short_name.short_description = 'Формулировка'

    def parent_code(self, obj):
        return obj.parent.code if obj.parent else '—'
    parent_code.short_description = 'Родитель'

    def task_count(self, obj):
        count = obj.get_task_count()
        return count if count else '—'
    task_count.short_description = 'Заданий'



@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'codifier', 'cognitive_level']
    list_filter = ['codifier', 'cognitive_level']
    search_fields = ['code', 'name']
    autocomplete_fields = ['codifier']
    filter_horizontal = ['tasks']
