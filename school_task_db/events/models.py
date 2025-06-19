from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import BaseModel
import os

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
    
    def get_student_groups(self):
        """Получить уникальные классы участников"""
        groups = set()
        for participation in self.eventparticipation_set.select_related('student').all():
            student_groups = participation.student.studentgroup_set.all()
            groups.update(student_groups)
        return list(groups)
    
    def get_participants_count(self):
        """Количество участников"""
        return self.students.count()
    
    def get_completed_count(self):
        """Количество выполненных работ"""
        return self.eventparticipation_set.filter(
            status__in=['completed', 'graded']
        ).count()
    
    def get_graded_count(self):
        """Количество проверенных работ"""
        return self.eventparticipation_set.filter(status='graded').count()
    
    def get_progress_percentage(self):
        """Процент выполнения события"""
        total = self.get_participants_count()
        if total == 0:
            return 0
        completed = self.get_completed_count()
        return round((completed / total) * 100, 1)
    
    def assign_variants_randomly(self):
        """Назначить варианты случайным образом"""
        from works.models import Variant
        import random
        
        variants = list(Variant.objects.filter(work=self.work))
        if not variants:
            return False
            
        participations = self.eventparticipation_set.filter(variant__isnull=True)
        
        for participation in participations:
            variant = random.choice(variants)
            participation.variant = variant
            participation.save()
        
        return True

class EventParticipation(BaseModel):
    """Участие ученика в событии (промежуточная модель)"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name='Событие')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, verbose_name='Ученик')
    variant = models.ForeignKey('works.Variant', on_delete=models.CASCADE, 
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
                                 help_text='{"task_id": {"points": 2, "max_points": 3, "comment": "..."}}')
    
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
    
    def get_percentage(self):
        """Процент выполнения"""
        if self.points and self.max_points and self.max_points > 0:
            return round((self.points / self.max_points) * 100, 1)
        return None
    
    def get_grade_color(self):
        """CSS класс для оценки"""
        if self.score:
            if self.score == 5:
                return 'success'
            elif self.score == 4:
                return 'info'
            elif self.score == 3:
                return 'warning'
            else:
                return 'danger'
        return 'secondary'
    
    # Удобные свойства для доступа
    @property
    def student(self):
        return self.participation.student
    
    @property
    def event(self):
        return self.participation.event
    
    @property
    def variant(self):
        return self.participation.variant
    
    @property
    def work(self):
        return self.participation.event.work
    
    def clean(self):
        """Валидация отметки"""
        if self.score and (self.score < 1 or self.score > 5):
            raise ValidationError('Оценка должна быть от 1 до 5')
        
        if self.points and self.max_points and self.points > self.max_points:
            raise ValidationError('Набранные баллы не могут превышать максимум')
