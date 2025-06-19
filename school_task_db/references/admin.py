from django.contrib import admin
from .models import SimpleReference, SubjectReference

@admin.register(SimpleReference)
class SimpleReferenceAdmin(admin.ModelAdmin):
    list_display = ['category', 'items_count', 'is_active']
    list_filter = ['category', 'is_active']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['category', 'is_active']
        }),
        ('Элементы справочника', {
            'fields': ['items_text'],
            'description': '<p>Введите каждый элемент с новой строки.</p>'
                          '<p><strong>Пример:</strong><br>'
                          'Расчётная задача<br>'
                          'Качественная задача<br>'
                          'Теоретический вопрос</p>'
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def items_count(self, obj):
        """Показать количество элементов"""
        count = len(obj.get_items_list())
        return f"{count} элементов"
    items_count.short_description = 'Количество'
    
    def has_add_permission(self, request):
        # Можно создать только справочники из предопределенного списка
        return True
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # При редактировании
            readonly.append('category')  # Нельзя менять категорию
        return readonly

@admin.register(SubjectReference)
class SubjectReferenceAdmin(admin.ModelAdmin):
    list_display = ['subject', 'category', 'items_count', 'is_active']
    list_filter = ['subject', 'category', 'is_active']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['subject', 'category', 'is_active']
        }),
        ('Элементы кодификатора', {
            'fields': ['items_text'],
            'description': '<p>Два формата записи:</p>'
                          '<p><strong>С кодами:</strong><br>'
                          '1.1|Натуральные числа<br>'
                          '1.2|Дроби</p>'
                          '<p><strong>Без кодов:</strong><br>'
                          'Натуральные числа<br>'
                          'Дроби</p>'
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def items_count(self, obj):
        """Показать количество элементов"""
        count = len(obj.get_items_dict())
        return f"{count} элементов"
    items_count.short_description = 'Количество'
