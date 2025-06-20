from django.db import models
from core.models import BaseModel

class SimpleReference(BaseModel):
    """
    Простой справочник - список значений через строки
    Учитель редактирует список в текстовом поле
    """
    
    CATEGORIES = [
        ('task_types', 'Типы заданий'),
        ('difficulty_levels', 'Уровни сложности'),
        ('cognitive_levels', 'Когнитивные уровни'),
        ('work_types', 'Типы работ'),
        ('subjects', 'Предметы'),
        ('comment_categories', 'Категории комментариев'),
    ]
    
    category = models.CharField(
        'Категория', 
        max_length=50, 
        choices=CATEGORIES, 
        unique=True,
        help_text='Тип справочника'
    )
    
    items_text = models.TextField(
        'Элементы справочника', 
        help_text='Каждый элемент с новой строки.\n'
                  'Пример:\nРасчётная задача\nКачественная задача\nТеоретический вопрос',
        blank=True
    )
    
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'
        ordering = ['category']
    
    def __str__(self):
        return f"{self.get_category_display()}"
    
    def get_items_list(self):
        """Получить список элементов из текста"""
        if not self.items_text:
            return []
        
        lines = self.items_text.strip().split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if line:  # Игнорируем пустые строки
                items.append(line)
        
        return items
    
    def get_choices(self):
        """Получить choices для Django форм: [(value, label), ...]"""
        items = self.get_items_list()
        return [(item, item) for item in items]
    
    def get_choices_with_empty(self):
        """Получить choices с пустым значением"""
        choices = [('', '--- Выберите ---')]
        choices.extend(self.get_choices())
        return choices

class SubjectReference(BaseModel):
    """
    Справочник кодификатора по предмету
    Формат: код|название ИЛИ просто название
    """
    
    # УБИРАЕМ hardcoded SUBJECT_CHOICES, делаем обычное поле
    subject = models.CharField(
        'Предмет', 
        max_length=100,
        help_text='Предмет из справочника предметов'
    )
    
    # ДОБАВЛЯЕМ поле для класса
    grade_level = models.CharField(
        'Класс', 
        max_length=50, 
        blank=True,
        help_text='Класс (например: 5, 7-9, 10-11). Если пусто - для всех классов'
    )
    
    CATEGORIES = [
        ('content_elements', 'Элементы содержания'),
        ('requirement_elements', 'Элементы требований'),
    ]
    
    category = models.CharField('Категория', max_length=50, choices=CATEGORIES)
    
    items_text = models.TextField(
        'Элементы кодификатора',
        help_text='Формат: код|название (каждый с новой строки)\n'
                  'Пример:\n1.1|Натуральные числа\n1.2|Дроби\n'
                  'Или просто:\nНатуральные числа\nДроби',
        blank=True
    )
    
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        verbose_name = 'Справочник кодификатора'
        verbose_name_plural = 'Справочники кодификатора'
        # ОБНОВЛЯЕМ unique_together с учетом нового поля
        unique_together = ['subject', 'grade_level', 'category']
        ordering = ['subject', 'grade_level', 'category']
    
    def __str__(self):
        # ОБНОВЛЯЕМ метод __str__ с учетом класса
        grade_part = f" ({self.grade_level})" if self.grade_level else " (все классы)"
        return f"{self.subject}{grade_part} - {self.get_category_display()}"
    
    # Остальные методы остаются без изменений
    def get_items_dict(self):
        """Получить словарь {код: название}"""
        if not self.items_text:
            return {}
        
        items = {}
        lines = self.items_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '|' in line:
                # Формат: код|название
                parts = line.split('|', 1)
                if len(parts) == 2:
                    code = parts[0].strip()
                    name = parts[1].strip()
                    if code and name:
                        items[code] = name
            else:
                # Простой формат: только название (код = название)
                items[line] = line
        
        return items
    
    def get_choices(self):
        """Получить choices для Django форм"""
        items = self.get_items_dict()
        return [(code, name) for code, name in items.items()]
    
    def get_choices_with_empty(self):
        """Получить choices с пустым значением"""
        choices = [('', '--- Выберите ---')]
        choices.extend(self.get_choices())
        return choices

