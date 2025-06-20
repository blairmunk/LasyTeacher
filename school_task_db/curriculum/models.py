from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import BaseModel

class Topic(BaseModel):
    """Основная тема (без иерархии)"""
    name = models.CharField('Название темы', max_length=200)
    subject = models.CharField('Предмет', max_length=100, 
                         help_text='Предмет из справочника предметов')
    section = models.CharField('Тематический раздел', max_length=200)
    grade_level = models.PositiveIntegerField('Класс', help_text='7, 8, 9, 10, 11')
    
    order = models.PositiveIntegerField('Порядок изучения', default=1)
    description = models.TextField('Описание темы', blank=True)
    difficulty_level = models.PositiveIntegerField('Базовый уровень сложности', choices=[
        (1, 'Базовый'),
        (2, 'Повышенный'),
        (3, 'Углубленный')
    ], default=1)
    
    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'
        ordering = ['subject', 'grade_level', 'section', 'order']
        unique_together = ['name', 'subject', 'grade_level', 'section']
    
    def __str__(self):
        # ИСПРАВЛЕННЫЙ метод __str__ без get_level()
        return f"[{self.get_short_uuid()}] {self.subject} {self.grade_level}кл: {self.section} → {self.name}"
    
    def get_absolute_url(self):
        return reverse('curriculum:topic-detail', kwargs={'pk': self.pk})
    
    def get_subtopics(self):
        """Получить все подтемы этой темы"""
        return self.subtopics.all().order_by('order')
    
    def get_subtopics_count(self):
        """Количество подтем"""
        return self.subtopics.count()

class SubTopic(BaseModel):
    """Подтема - простая связь с темой"""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, 
                             related_name='subtopics', verbose_name='Основная тема')
    name = models.CharField('Название подтемы', max_length=200)
    description = models.TextField('Описание подтемы', blank=True)
    order = models.PositiveIntegerField('Порядок в теме', default=1)
    
    class Meta:
        verbose_name = 'Подтема'
        verbose_name_plural = 'Подтемы'
        ordering = ['topic', 'order']
        unique_together = ['topic', 'name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.topic.name} → {self.name}"
    
    def get_absolute_url(self):
        return reverse('curriculum:subtopic-detail', kwargs={'pk': self.pk})
    
    # Свойства для удобства доступа к данным темы
    @property
    def subject(self):
        return self.topic.subject
    
    @property
    def grade_level(self):
        return self.topic.grade_level
    
    @property
    def section(self):
        return self.topic.section
    
    def clean(self):
        """Валидация подтемы"""
        if not self.topic:
            raise ValidationError('Подтема должна принадлежать основной теме')

class Course(BaseModel):
    """Курс - набор работ для изучения"""
    name = models.CharField('Название курса', max_length=200)
    description = models.TextField('Описание курса', blank=True)
    
    # Основные параметры
    subject = models.CharField('Предмет', max_length=100, 
                             help_text='Предмет из справочника предметов')
    grade_level = models.PositiveIntegerField('Класс')
    academic_year = models.CharField('Учебный год', max_length=20, default='2024-2025')
    
    # Временные параметры
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    total_hours = models.PositiveIntegerField('Общее количество часов', null=True, blank=True)
    hours_per_week = models.PositiveIntegerField('Часов в неделю', default=2)
    
    # Статус
    is_active = models.BooleanField('Активный', default=True)
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['grade_level', 'subject', 'name']
        unique_together = ['name', 'subject', 'grade_level', 'academic_year']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.subject} {self.grade_level} класс - {self.name}"
    
    def get_absolute_url(self):
        return reverse('curriculum:course-detail', kwargs={'pk': self.pk})
    
    def get_covered_topics(self):
        """Темы, покрываемые курсом (через работы)"""
        from tasks.models import Task
        from django.db.models import Q
        
        # Получаем все задания из всех работ курса
        tasks = Task.objects.filter(
            Q(taskgroup__analog_group__workanaloggroup__work__courseassignment__course=self)
        ).distinct()
        
        # Извлекаем уникальные темы
        topics = set()
        for task in tasks:
            if task.topic:
                topics.add(task.topic)
        
        return list(topics)
    
    def get_works(self):
        """Работы курса"""
        return self.courseassignment_set.all().order_by('order')

class CourseAssignment(BaseModel):
    """Назначение работы в курс"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    work = models.ForeignKey('works.Work', on_delete=models.CASCADE, verbose_name='Работа')
    order = models.PositiveIntegerField('Порядок в курсе', default=1)
    planned_date = models.DateField('Запланированная дата', null=True, blank=True)
    weight = models.FloatField('Вес в итоговой оценке', default=1.0)
    
    class Meta:
        verbose_name = 'Работа в курсе'
        verbose_name_plural = 'Работы в курсах'
        unique_together = ['course', 'work']
        ordering = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.name} → {self.work.name}"
