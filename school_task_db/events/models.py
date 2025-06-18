from django.db import models
from django.urls import reverse
from core.models import BaseModel

class Event(BaseModel):
    """Событие (проведение работы)"""
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('conducted', 'Проведено'),
        ('checked', 'Проверено'),
        ('graded', 'Оценено'),
        ('closed', 'Закрыто'),
    ]
    
    name = models.CharField('Название события', max_length=200)
    date = models.DateTimeField('Дата проведения')
    work = models.ForeignKey('works.Work', on_delete=models.CASCADE, verbose_name='Работа')
    student_group = models.ForeignKey('students.StudentGroup', on_delete=models.CASCADE, verbose_name='Класс')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='planned')
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.name} - {self.student_group.name}"
    
    def get_absolute_url(self):
        return reverse('events:detail', kwargs={'pk': self.pk})

class Mark(BaseModel):
    """Отметка"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, verbose_name='Ученик')
    variant = models.ForeignKey('works.Variant', on_delete=models.CASCADE, verbose_name='Вариант')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name='Событие', null=True, blank=True)
    score = models.PositiveIntegerField('Оценка', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Отметка'
        verbose_name_plural = 'Отметки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.variant} - {self.score or 'Не оценено'}"
