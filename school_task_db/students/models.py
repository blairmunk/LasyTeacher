from django.db import models
from django.urls import reverse
from core.models import BaseModel

class Student(BaseModel):
    """Ученик"""
    first_name = models.CharField('Имя', max_length=50)
    last_name = models.CharField('Фамилия', max_length=50)
    middle_name = models.CharField('Отчество', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    
    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.get_full_name()}"
    
    def get_absolute_url(self):
        return reverse('students:detail', kwargs={'pk': self.pk})
    
    def get_full_name(self):
        """Полное имя ученика"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)
    
    def get_short_name(self):
        """Краткое имя (Фамилия И.О.)"""
        result = self.last_name
        if self.first_name:
            result += f" {self.first_name[0]}."
        if self.middle_name:
            result += f"{self.middle_name[0]}."
        return result

class StudentGroup(BaseModel):
    """Класс"""
    name = models.CharField('Название класса', max_length=10)
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.PROTECT,
        verbose_name='Учебный год',
        related_name='student_groups',
        null=True, blank=True,
    )
    students = models.ManyToManyField(Student, verbose_name='Ученики', blank=True)

    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        ordering = ['name']
        unique_together = ['name', 'academic_year']

    def __str__(self):
        year_str = f" ({self.academic_year.name})" if self.academic_year else ""
        return f"{self.name}{year_str}"

    def get_absolute_url(self):
        return reverse('students:group-detail', kwargs={'pk': self.pk})
    
    def get_students_count(self):
        """Количество учеников в классе"""
        return self.students.count()
    
    def get_active_students(self):
        """Получить активных учеников класса"""
        return self.students.all().order_by('last_name', 'first_name')
    
    def get_grade_level(self):
        """Извлечь номер класса из названия"""
        try:
            return int(self.name[0]) if self.name and self.name[0].isdigit() else None
        except (ValueError, IndexError):
            return None

class StudentTaskLog(BaseModel):
    """Лог: ученик X выполнил задание Y с результатом Z.
    
    Денормализованная таблица для быстрых запросов:
    - Работа над ошибками (exclude выполненных)
    - Тепловые карты по темам/группам
    - Прогресс ученика
    """
    
    # Кто и что
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='task_log', verbose_name='Ученик'
    )
    task = models.ForeignKey(
        'tasks.Task', on_delete=models.CASCADE,
        related_name='student_log', verbose_name='Задание'
    )
    
    # Контекст выполнения
    event = models.ForeignKey(
        'events.Event', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Событие'
    )
    variant = models.ForeignKey(
        'works.Variant', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Вариант'
    )
    mark = models.ForeignKey(
        'events.Mark', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Отметка'
    )
    
    # Кэш для быстрых запросов (денормализация)
    topic = models.ForeignKey(
        'curriculum.Topic', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Тема (кэш)'
    )
    analog_group = models.ForeignKey(
        'task_groups.AnalogGroup', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Группа аналогов (кэш)'
    )
    difficulty = models.IntegerField('Сложность (кэш)', null=True, blank=True)
    
    # Результат
    points = models.FloatField('Набранные баллы', null=True, blank=True)
    max_points = models.FloatField('Макс. баллы', null=True, blank=True)
    is_correct = models.BooleanField('Выполнено верно', null=True, blank=True)
    percentage = models.FloatField('Процент выполнения', null=True, blank=True)
    
    # Комментарий учителя к конкретному заданию
    comment = models.TextField('Комментарий', blank=True, default='')
    
    # Дата выполнения (может отличаться от created_at)
    completed_at = models.DateTimeField('Дата выполнения')
    
    class Meta:
        verbose_name = 'Выполненное задание'
        verbose_name_plural = 'Выполненные задания'
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['student', 'task']),
            models.Index(fields=['student', 'topic']),
            models.Index(fields=['student', 'analog_group']),
            models.Index(fields=['student', 'completed_at']),
            models.Index(fields=['task', 'is_correct']),
            models.Index(fields=['student', 'is_correct']),
        ]
    
    def __str__(self):
        result = f"{self.percentage:.0f}%" if self.percentage is not None else "?"
        return f"[{self.get_short_uuid()}] {self.student} → {self.task} [{result}]"
    
    def save(self, *args, **kwargs):
        # Авто-расчёт percentage и is_correct
        if self.points is not None and self.max_points and self.max_points > 0:
            self.percentage = round((self.points / self.max_points) * 100, 1)
            if self.is_correct is None:
                self.is_correct = self.percentage >= 70
        super().save(*args, **kwargs)
    
    @classmethod
    def update_from_mark(cls, mark):
        """Создать/обновить записи лога из Mark.task_scores JSON"""
        from tasks.models import Task
        
        participation = mark.participation
        student = participation.student
        event = participation.event
        variant = participation.variant
        
        task_scores = mark.task_scores or {}
        if not task_scores:
            return 0
        
        created_count = 0
        completed_at = mark.checked_at or mark.created_at
        
        for task_id_str, score_data in task_scores.items():
            try:
                task = Task.objects.select_related('topic').get(pk=task_id_str)
            except (Task.DoesNotExist, ValueError):
                continue
            
            # Кэш группы аналогов
            first_group = task.taskgroup_set.select_related('group').first()
            analog_group = first_group.group if first_group else None
            
            points = score_data.get('points')
            max_points = score_data.get('max_points')
            comment_text = score_data.get('comment', '')
            
            obj, created = cls.objects.update_or_create(
                student=student,
                task=task,
                event=event,
                defaults={
                    'variant': variant,
                    'mark': mark,
                    'topic': task.topic,
                    'analog_group': analog_group,
                    'difficulty': task.difficulty,
                    'points': points,
                    'max_points': max_points,
                    'comment': comment_text,
                    'completed_at': completed_at,
                }
            )
            if created:
                created_count += 1
        
        return created_count
