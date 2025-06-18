from django.db import models
import uuid

class BaseModel(models.Model):
    """Базовая модель с общими полями"""
    uuid = models.UUIDField('UUID', default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        abstract = True
    
    def get_short_uuid(self):
        """Возвращает последние 4 символа UUID для отображения"""
        return str(self.uuid)[-4:].upper()
    
    def get_medium_uuid(self):
        """Возвращает последние 8 символов UUID"""
        return str(self.uuid)[-8:].upper()
    
    def get_display_id(self):
        """Красивый ID для отображения пользователю"""
        return f"#{self.get_short_uuid()}"
    
    @classmethod
    def get_by_uuid(cls, uuid_str):
        """Поиск по полному или частичному UUID"""
        try:
            if len(uuid_str) == 36:
                # Полный UUID
                return cls.objects.get(uuid=uuid_str)
            elif len(uuid_str) >= 3:
                # Поиск по окончанию UUID (регистронезависимый)
                uuid_str = uuid_str.lower().replace('#', '')
                matches = cls.objects.filter(uuid__iendswith=uuid_str)
                if matches.count() == 1:
                    return matches.first()
                elif matches.count() > 1:
                    # Если найдено несколько, вернуть точное совпадение по последним символам
                    for obj in matches:
                        if str(obj.uuid)[-len(uuid_str):].lower() == uuid_str:
                            return obj
                return matches.first()
        except (cls.DoesNotExist, ValueError):
            pass
        return None

class BaseModelWithOrder(BaseModel):
    """Базовая модель с полем порядка"""
    order = models.PositiveIntegerField('Порядок', default=1)
    
    class Meta:
        abstract = True
        ordering = ['order', 'created_at']
