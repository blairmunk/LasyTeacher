from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import BaseModel
from core_logic.value_objects.mark_validation import validate_mark_values

def work_scan_upload_path(instance, filename):
    """Путь для загрузки сканов работ"""
    student_name = f"{instance.participation.student.last_name}_{instance.participation.student.first_name}"
    event_name = instance.participation.event.name.replace(' ', '_').replace('/', '_')
    return f'work_scans/{event_name}/{student_name}_{filename}'

class Event(BaseModel):
    """Событие (проведение работы) - привязано к ученикам, а не к классу"""
    name = models.CharField('Название события', max_length=200)
    work = models.ForeignKey('works.Work', on_delete=models.CASCADE, verbose_name='Работа')
    
    # НОВАЯ АРХИТЕКТУРА: связь с учениками напрямую через промежуточную модель
    students = models.ManyToManyField('students.Student', 
                                    through='EventParticipation',
                                    verbose_name='Участники')
    
    # Временные параметры
    planned_date = models.DateTimeField('Запланированная дата')
    actual_start = models.DateTimeField('Фактическое начало', null=True, blank=True)
    actual_end = models.DateTimeField('Фактическое окончание', null=True, blank=True)
    
    # Статус события
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('in_progress', 'Выполняется'),
        ('completed', 'Завершено'),
        ('reviewing', 'На проверке'),
        ('graded', 'Проверено'),
        ('closed', 'Закрыто'),
    ]
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Дополнительная информация
    course = models.ForeignKey('curriculum.Course', on_delete=models.SET_NULL,
                              null=True, blank=True, verbose_name='Курс')
    description = models.TextField('Описание события', blank=True)
    location = models.CharField('Место проведения', max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['-planned_date']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"
    
    def get_absolute_url(self):
        return reverse('events:detail', kwargs={'pk': self.pk})
    
class EventParticipation(BaseModel):
    """Участие ученика в событии (промежуточная модель)"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name='Событие')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, verbose_name='Ученик')
    variant = models.ForeignKey('works.Variant', on_delete=models.PROTECT,
                               null=True, blank=True, verbose_name='Назначенный вариант')
    
    # Статус участия
    PARTICIPATION_STATUS = [
        ('assigned', 'Назначено'),
        ('started', 'Начал выполнение'),
        ('completed', 'Завершил'),
        ('graded', 'Проверено'),
        ('absent', 'Отсутствовал'),
    ]
    status = models.CharField('Статус участия', max_length=20, 
                            choices=PARTICIPATION_STATUS, default='assigned')
    
    # Временные метки
    started_at = models.DateTimeField('Начал в', null=True, blank=True)
    completed_at = models.DateTimeField('Завершил в', null=True, blank=True)
    graded_at = models.DateTimeField('Проверено в', null=True, blank=True)
    
    # Место (если ученики в разных аудиториях)
    seat_number = models.CharField('Место', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Участие в событии'
        verbose_name_plural = 'Участие в событиях'
        unique_together = ['event', 'student']
        ordering = ['event', 'student']
    
    def __str__(self):
        return f"{self.student.get_full_name()} → {self.event.name}"
    
    def get_absolute_url(self):
        return reverse('events:participation-detail', kwargs={'pk': self.pk})

class Mark(BaseModel):
    """Отметка - результат выполнения работы учеником"""
    participation = models.OneToOneField(EventParticipation, on_delete=models.CASCADE, 
                                       verbose_name='Участие в событии')
    
    # Оценка
    score = models.PositiveIntegerField('Оценка', null=True, blank=True,
                                      help_text='Оценка от 1 до 5')
    points = models.PositiveIntegerField('Набранные баллы', null=True, blank=True)
    max_points = models.PositiveIntegerField('Максимум баллов', null=True, blank=True)
    
    # Файлы работы
    work_scan = models.FileField('Скан работы', upload_to=work_scan_upload_path, 
                               null=True, blank=True,
                               help_text='PDF скан выполненной работы')
    
    # Детализация по заданиям (JSON)
    task_scores = models.JSONField('Баллы по заданиям', default=dict, blank=True,
                                 help_text='{"variant_task_id": {"task_id": "...", "points": 2, "max_points": 3, "comment": "..."}}')
    
    # Комментарии учителя
    teacher_comment = models.TextField('Комментарий учителя', blank=True)
    mistakes_analysis = models.TextField('Анализ ошибок', blank=True)
    recommendations = models.TextField('Рекомендации', blank=True)
    
    # Временные метки и проверяющий
    checked_at = models.DateTimeField('Проверено в', null=True, blank=True)
    checked_by = models.CharField('Проверил', max_length=100, blank=True)
    
    # Дополнительные метки
    is_retake = models.BooleanField('Пересдача', default=False)
    is_excellent = models.BooleanField('Отличная работа', default=False)
    needs_attention = models.BooleanField('Требует внимания', default=False)
    
    class Meta:
        verbose_name = 'Отметка'
        verbose_name_plural = 'Отметки'
        ordering = ['-created_at']
    
    def __str__(self):
        score_str = f"{self.score}" if self.score else "не оценено"
        return f"[{self.get_short_uuid()}] {self.participation.student.get_full_name()} - {score_str}"
    
    def get_absolute_url(self):
        return reverse('events:mark-detail', kwargs={'pk': self.pk})
    
    def clean(self):
        try:
            validate_mark_values(
                score=self.score,
                points=self.points,
                max_points=self.max_points,
            )
        except ValueError as error:
            raise ValidationError(str(error)) from error


class AttemptSnapshot(BaseModel):
    """Immutable revision of one checked participation."""

    participation = models.ForeignKey(
        EventParticipation,
        on_delete=models.PROTECT,
        related_name='attempt_snapshots',
        verbose_name='Участие',
    )
    mark = models.ForeignKey(
        Mark,
        on_delete=models.PROTECT,
        related_name='attempt_snapshots',
        verbose_name='Проверка-источник',
    )
    revision = models.PositiveIntegerField('Ревизия')

    student_id_snapshot = models.CharField('ID ученика (снимок)', max_length=36)
    student_name_snapshot = models.CharField('Ученик (снимок)', max_length=300)
    event_id_snapshot = models.CharField('ID события (снимок)', max_length=36)
    event_name_snapshot = models.CharField('Событие (снимок)', max_length=200)
    event_date_snapshot = models.DateTimeField('Дата события (снимок)')
    work_id_snapshot = models.CharField('ID работы (снимок)', max_length=36)
    work_name_snapshot = models.CharField('Работа (снимок)', max_length=200)
    variant_id_snapshot = models.CharField(
        'ID варианта (снимок)',
        max_length=36,
        blank=True,
    )
    variant_number_snapshot = models.PositiveIntegerField(
        'Номер варианта (снимок)',
        null=True,
        blank=True,
    )

    score = models.PositiveIntegerField('Оценка', null=True, blank=True)
    points = models.DecimalField(
        'Набранные баллы',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_points = models.DecimalField(
        'Максимум баллов',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teacher_comment = models.TextField('Комментарий учителя', blank=True)
    mistakes_analysis = models.TextField('Анализ ошибок', blank=True)
    recommendations = models.TextField('Рекомендации', blank=True)
    checked_at_snapshot = models.DateTimeField(
        'Проверено в (снимок)',
        null=True,
        blank=True,
    )
    checked_by_snapshot = models.CharField(
        'Проверил (снимок)',
        max_length=100,
        blank=True,
    )
    is_retake = models.BooleanField('Пересдача', default=False)
    is_excellent = models.BooleanField('Отличная работа', default=False)
    needs_attention = models.BooleanField('Требует внимания', default=False)
    task_scores_snapshot = models.JSONField(
        'Баллы по заданиям (снимок)',
        default=dict,
        blank=True,
    )

    class Meta:
        verbose_name = 'Снимок проверенной попытки'
        verbose_name_plural = 'Снимки проверенных попыток'
        ordering = ['participation_id', '-revision']
        constraints = [
            models.UniqueConstraint(
                fields=['participation', 'revision'],
                name='unique_attempt_snapshot_revision',
            ),
        ]

    def __str__(self):
        return f'{self.student_name_snapshot}: {self.event_name_snapshot} · r{self.revision}'


class AttemptTaskSnapshot(BaseModel):
    """Checked result for one immutable task slot in an attempt revision."""

    attempt = models.ForeignKey(
        AttemptSnapshot,
        on_delete=models.CASCADE,
        related_name='task_results',
        verbose_name='Снимок попытки',
    )
    variant_task = models.ForeignKey(
        'works.VariantTask',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='attempt_task_snapshots',
        verbose_name='Задание варианта',
    )
    task_id_snapshot = models.CharField('ID задания (снимок)', max_length=36)
    task_content_snapshot = models.JSONField(
        'Содержимое задания (снимок)',
        default=dict,
    )
    source_selection_id_snapshot = models.CharField(
        'Блок спецификации (снимок)',
        max_length=36,
        blank=True,
        default='',
    )
    content_order_snapshot = models.PositiveIntegerField(
        'Порядок блока спецификации (снимок)',
        default=0,
    )
    order_snapshot = models.PositiveIntegerField('Номер задания (снимок)')
    is_assessable_snapshot = models.BooleanField('Оценивалось (снимок)')
    expected_max_points_snapshot = models.DecimalField(
        'Максимум по варианту (снимок)',
        max_digits=8,
        decimal_places=2,
    )
    points = models.DecimalField(
        'Набранные баллы',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    checked_max_points = models.DecimalField(
        'Максимум при проверке',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Результат задания в снимке попытки'
        verbose_name_plural = 'Результаты заданий в снимках попыток'
        ordering = ['order_snapshot', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'variant_task'],
                name='unique_attempt_snapshot_variant_task',
            ),
            models.UniqueConstraint(
                fields=['attempt', 'task_id_snapshot'],
                condition=models.Q(variant_task__isnull=True),
                name='unique_attempt_snapshot_legacy_task',
            ),
        ]

    def __str__(self):
        return f'{self.attempt} · № {self.order_snapshot}'
