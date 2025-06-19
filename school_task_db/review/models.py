from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel

class ReviewSession(BaseModel):
    """Сессия проверки - группировка проверок для аналитики"""
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Проверяющий')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, verbose_name='Событие')
    started_at = models.DateTimeField('Начало проверки', auto_now_add=True)
    finished_at = models.DateTimeField('Окончание проверки', null=True, blank=True)
    
    # Статистика сессии
    total_participations = models.PositiveIntegerField('Всего работ', default=0)
    checked_participations = models.PositiveIntegerField('Проверено работ', default=0)
    average_time_per_work = models.DurationField('Среднее время на работу', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Сессия проверки'
        verbose_name_plural = 'Сессии проверки'
    
    def __str__(self):
        return f"Проверка {self.event.name} - {self.reviewer.get_full_name()}"
    
    @property
    def progress_percentage(self):
        if self.total_participations == 0:
            return 0
        return round((self.checked_participations / self.total_participations) * 100, 1)
    
    @property
    def is_completed(self):
        return self.finished_at is not None

class ReviewComment(BaseModel):
    """Типовые комментарии для быстрого использования"""
    text = models.TextField('Текст комментария')
    category = models.CharField('Категория', max_length=50, choices=[
        ('excellent', 'Отличная работа'),
        ('good', 'Хорошая работа'),
        ('needs_improvement', 'Требует улучшения'),
        ('mistake', 'Типичная ошибка'),
        ('suggestion', 'Рекомендация'),
    ])
    is_active = models.BooleanField('Активный', default=True)
    usage_count = models.PositiveIntegerField('Количество использований', default=0)
    
    class Meta:
        verbose_name = 'Типовой комментарий'
        verbose_name_plural = 'Типовые комментарии'
        ordering = ['-usage_count', 'category']
    
    def __str__(self):
        return f"[{self.get_category_display()}] {self.text[:50]}..."
