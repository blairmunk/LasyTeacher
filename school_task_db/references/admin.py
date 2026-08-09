from django.contrib import admin
from django import forms
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

# НОВАЯ кастомная форма для SubjectReference
class SubjectReferenceAdminForm(forms.ModelForm):
    """Форма админки с динамическим выбором предмета"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Динамически загружаем предметы из справочника subjects
        subject_reference = SimpleReference.objects.filter(
            category='subjects',
            is_active=True,
        ).first()
        if subject_reference and subject_reference.get_items_list():
            self.fields['subject'] = forms.ChoiceField(
                label='Предмет',
                choices=subject_reference.get_choices_with_empty(),
                widget=forms.Select(attrs={'class': 'form-select'}),
            )
        
        # Настраиваем поле класса
        self.fields['grade_level'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Например: 5, 7-9, 10-11'
        })
    
    class Meta:
        model = SubjectReference
        fields = '__all__'


# ОБНОВЛЯЕМ SubjectReferenceAdmin
@admin.register(SubjectReference)
class SubjectReferenceAdmin(admin.ModelAdmin):
    form = SubjectReferenceAdminForm  # ДОБАВЛЯЕМ кастомную форму
    
    # ОБНОВЛЯЕМ list_display с новым полем
    list_display = ['subject', 'grade_level_display', 'category', 'items_count', 'is_active']
    list_filter = ['subject', 'category', 'is_active']  # Убираем grade_level из фильтра пока
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    # ОБНОВЛЯЕМ fieldsets с новым полем
    fieldsets = [
        ('Основная информация', {
            'fields': ['subject', 'grade_level', 'category', 'is_active'],
            'description': 'Выберите предмет из справочника и укажите класс(ы)'
        }),
        ('Элементы кодификатора', {
            'fields': ['items_text'],
            'description': '<p><strong>Формат записи:</strong></p>'
                          '<p><strong>С кодами:</strong> 1.1|Натуральные числа</p>'
                          '<p><strong>Без кодов:</strong> Натуральные числа</p>'
                          '<p><em>Каждый элемент с новой строки</em></p>'
        }),
        ('Служебная информация', {
            'fields': ['uuid', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    # НОВЫЙ метод для отображения класса
    def grade_level_display(self, obj):
        """Красивое отображение класса"""
        if obj.grade_level:
            return obj.grade_level
        return '🌐 Все классы'
    grade_level_display.short_description = 'Класс'
    
    def items_count(self, obj):
        """Показать количество элементов"""
        count = len(obj.get_items_dict())
        if count > 0:
            return f"📋 {count} элементов"
        return "📋 Пусто"
    items_count.short_description = 'Количество'
    
    def get_form(self, request, obj=None, **kwargs):
        """Добавляем подсказки в форму"""
        form = super().get_form(request, obj, **kwargs)
        
        # Добавляем help_text для grade_level
        if 'grade_level' in form.base_fields:
            form.base_fields['grade_level'].help_text = (
                'Примеры: "5", "7-9", "10-11", "5-6". '
                'Оставьте пустым для всех классов.'
            )
        
        return form
