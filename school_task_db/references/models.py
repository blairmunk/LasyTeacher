from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel

class ReferenceCategory(BaseModel):
    """Категории справочников"""
    code = models.CharField('Код категории', max_length=50, unique=True,
                           help_text='Уникальный код для программного доступа')
    name = models.CharField('Название категории', max_length=100)
    description = models.TextField('Описание', blank=True)
    is_system = models.BooleanField('Системная категория', default=False,
                                   help_text='Системные категории нельзя удалять')
    is_active = models.BooleanField('Активна', default=True)
    
    class Meta:
        verbose_name = 'Категория справочника'
        verbose_name_plural = 'Категории справочников'
        ordering = ['name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"
    
    def clean(self):
        if self.code:
            self.code = self.code.lower().replace(' ', '_')

class ReferenceItem(BaseModel):
    """Элемент справочника"""
    category = models.ForeignKey(ReferenceCategory, on_delete=models.CASCADE,
                                verbose_name='Категория', related_name='items')
    code = models.CharField('Код', max_length=50,
                           help_text='Уникальный код в рамках категории')
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    order = models.PositiveIntegerField('Порядок сортировки', default=100)
    is_active = models.BooleanField('Активен', default=True)
    
    # Дополнительные поля для гибкости
    numeric_value = models.IntegerField('Числовое значение', null=True, blank=True,
                                       help_text='Для уровней сложности, классов и т.п.')
    color = models.CharField('Цвет', max_length=7, blank=True,
                           help_text='HEX код цвета для отображения (#FF0000)')
    icon = models.CharField('Иконка', max_length=50, blank=True,
                          help_text='CSS класс иконки (например: fas fa-star)')
    
    # JSON поле для дополнительных настроек
    extra_data = models.JSONField('Дополнительные данные', default=dict, blank=True,
                                 help_text='JSON с дополнительными параметрами')
    
    class Meta:
        verbose_name = 'Элемент справочника'
        verbose_name_plural = 'Элементы справочников'
        unique_together = ['category', 'code']
        ordering = ['category', 'order', 'name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.category.name}: {self.name}"
    
    def clean(self):
        if self.code:
            self.code = self.code.lower().replace(' ', '_')
        
        if self.color and not self.color.startswith('#'):
            self.color = f"#{self.color}"
    
    def get_display_with_icon(self):
        """Возвращает название с иконкой"""
        if self.icon:
            return f'<i class="{self.icon}"></i> {self.name}'
        return self.name

# Менеджер для удобного получения choices
class ReferenceManager:
    """Утилиты для работы со справочниками"""
    
    @staticmethod
    def get_choices(category_code, include_empty=False):
        """Получить choices для Django поля"""
        try:
            category = ReferenceCategory.objects.get(code=category_code, is_active=True)
            items = ReferenceItem.objects.filter(
                category=category, 
                is_active=True
            ).order_by('order', 'name')
            
            choices = [(item.code, item.name) for item in items]
            
            if include_empty:
                choices.insert(0, ('', '--- Выберите ---'))
                
            return choices
        except ReferenceCategory.DoesNotExist:
            return [('', 'Категория не найдена')] if include_empty else []
    
    @staticmethod
    def get_numeric_choices(category_code, include_empty=False):
        """Получить choices с числовыми значениями"""
        try:
            category = ReferenceCategory.objects.get(code=category_code, is_active=True)
            items = ReferenceItem.objects.filter(
                category=category,
                is_active=True,
                numeric_value__isnull=False
            ).order_by('numeric_value')
            
            choices = [(item.numeric_value, item.name) for item in items]
            
            if include_empty:
                choices.insert(0, (None, '--- Выберите ---'))
                
            return choices
        except ReferenceCategory.DoesNotExist:
            return [(None, 'Категория не найдена')] if include_empty else []
    
    @staticmethod
    def get_item(category_code, item_code):
        """Получить конкретный элемент справочника"""
        try:
            return ReferenceItem.objects.get(
                category__code=category_code,
                code=item_code,
                is_active=True
            )
        except ReferenceItem.DoesNotExist:
            return None
    
    @staticmethod
    def get_category_items(category_code):
        """Получить все активные элементы категории"""
        try:
            category = ReferenceCategory.objects.get(code=category_code, is_active=True)
            return ReferenceItem.objects.filter(
                category=category,
                is_active=True
            ).order_by('order', 'name')
        except ReferenceCategory.DoesNotExist:
            return ReferenceItem.objects.none()
