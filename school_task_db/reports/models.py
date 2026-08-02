from django.db import models

from core.models import BaseModel


class EventReportNarrativeModel(BaseModel):
    """Teacher-authored narrative for a live event performance report."""

    event = models.OneToOneField(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='performance_report_narrative',
        verbose_name='Событие',
    )
    possible_causes = models.TextField('Возможные причины ошибок', blank=True)
    recommendations = models.TextField('Рекомендации', blank=True)
    planned_actions = models.TextField('Запланированные мероприятия', blank=True)
    additional_notes = models.TextField('Дополнительные примечания', blank=True)

    class Meta:
        verbose_name = 'Текст отчёта по событию'
        verbose_name_plural = 'Тексты отчётов по событиям'

    def __str__(self):
        return f'Отчёт: {self.event.name}'
