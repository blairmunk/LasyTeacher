from django.db import models


class BaseModel(models.Model):
    """Базовая модель с общими полями"""
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        abstract = True


class BaseModelWithOrder(BaseModel):
    """Базовая модель с полем порядка"""
    order = models.PositiveIntegerField('Порядок', default=1)
    
    class Meta:
        abstract = True
        ordering = ['order', 'created_at']