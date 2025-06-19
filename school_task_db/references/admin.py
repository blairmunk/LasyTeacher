from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ReferenceCategory, ReferenceItem

class ReferenceItemInline(admin.TabularInline):
    model = ReferenceItem
    extra = 1
    fields = ['code', 'name', 'numeric_value', 'order', 'is_active', 'color', 'icon']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.category and obj.category.is_system:
            return ['code']  # Код системных элементов нельзя менять
        return []

@admin.register(ReferenceCategory)
class ReferenceCategoryAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'code', 'items_count', 'is_system', 'is_active']
    list_filter = ['is_system', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['uuid', 'get_short_uuid', 'created_at', 'updated_at']
    inlines = [ReferenceItemInline]
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'code', 'description']
        }),
        ('Настройки', {
            'fields': ['is_system', 'is_active']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def items_count(self, obj):
        count = obj.items.count()
        if count > 0:
            url = reverse('admin:references_referenceitem_changelist')
            return format_html(
                '<a href="{}?category__id__exact={}">{} элементов</a>',
                url, obj.id, count
            )
        return '0 элементов'
    items_count.short_description = 'Количество элементов'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.is_system:
            readonly.extend(['code', 'is_system'])
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(ReferenceItem)
class ReferenceItemAdmin(admin.ModelAdmin):
    list_display = ['get_short_uuid', 'name', 'category', 'code', 'numeric_value', 
                    'get_color_display', 'order', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'category__name', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['category', 'order']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['category', 'name', 'code', 'description']
        }),
        ('Значения и настройки', {
            'fields': ['numeric_value', 'order', 'is_active']
        }),
        ('Отображение', {
            'fields': ['color', 'icon'],
            'classes': ['collapse']
        }),
        ('Дополнительные данные', {
            'fields': ['extra_data'],
            'classes': ['collapse']
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'get_short_uuid', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['uuid', 'get_short_uuid', 'created_at', 'updated_at']
    
    def get_short_uuid(self, obj):
        return obj.get_short_uuid()
    get_short_uuid.short_description = 'UUID'
    
    def get_color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
                obj.color, obj.color
            )
        return '—'
    get_color_display.short_description = 'Цвет'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.category and obj.category.is_system:
            readonly.append('code')
        return readonly

# Дополнительная настройка админки
admin.site.index_template = 'admin/custom_index.html'
