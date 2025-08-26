# core/models.py
from django.db import models
import uuid

class BaseModel(models.Model):
    """Базовая модель с UUID как primary key"""
    # ИЗМЕНЕНО: UUID стал primary key
    id = models.UUIDField('ID', primary_key=True, default=uuid.uuid4, editable=False)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        abstract = True
    
    def get_short_uuid(self):
        """Возвращает последние 4 символа UUID для отображения"""
        return str(self.id)[-4:].upper()
    
    def get_medium_uuid(self):
        """Возвращает последние 8 символов UUID"""
        return str(self.id)[-8:].upper()
    
    def get_display_id(self):
        """Красивый ID для отображения пользователю"""
        return f"#{self.get_short_uuid()}"
    
    @classmethod
    def get_by_uuid(cls, uuid_str):
        """УПРОЩЕНО: теперь UUID = primary key"""
        try:
            if len(uuid_str) == 36:
                # Полный UUID
                return cls.objects.get(id=uuid_str)  # id теперь UUID
            elif len(uuid_str) >= 3:
                # Поиск по окончанию UUID
                uuid_str = uuid_str.lower().replace('#', '')
                matches = cls.objects.filter(id__iendswith=uuid_str)
                return matches.first() if matches.count() == 1 else None
        except (cls.DoesNotExist, ValueError):
            pass
        return None
    
    # НОВОЕ: удобные методы для совместимости
    @property
    def uuid(self):
        """Алиас для совместимости со старым кодом"""
        return self.id
    
    @property
    def pk(self):
        """Primary key - теперь UUID"""
        return self.id


class BaseModelWithOrder(BaseModel):
    """Базовая модель с полем порядка"""
    order = models.PositiveIntegerField('Порядок', default=1)
    
    class Meta:
        abstract = True
        ordering = ['order', 'created_at']
