from django.db import models
from django.urls import reverse

from core_logic.value_objects.variant_print_plan import (
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_SPECIFIC_CHOICES,
)
from core.models import BaseModel

from tasks.models import Task
import statistics


class AnalogGroup(BaseModel):
    """Группа аналогичных заданий"""
    name = models.CharField('Название группы', max_length=200)
    description = models.TextField('Описание', blank=True)
    difficulty = models.IntegerField(
        'Номинальная сложность',
        choices=Task.DIFFICULTY_LEVELS,
        default=0,
        help_text='0 = авто-определение из медианы заданий'
    )

    class Meta:
        verbose_name = 'Группа аналогичных заданий'
        verbose_name_plural = 'Группы аналогичных заданий'
        ordering = ['name']

    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"

    def get_absolute_url(self):
        return reverse('task_groups:detail', kwargs={'pk': self.pk})

    @property
    def effective_difficulty(self):
        """Номинальная сложность: явная или медиана из заданий"""
        if self.difficulty and self.difficulty > 0:
            return self.difficulty
        difficulties = list(
            self.taskgroup_set.values_list('task__difficulty', flat=True)
        )
        if difficulties:
            return round(statistics.median(difficulties))
        return 3  # fallback

    @property
    def difficulty_display(self):
        """Отображение сложности с пометкой авто"""
        d = self.effective_difficulty
        label = dict(Task.DIFFICULTY_LEVELS).get(d, '?')
        if self.difficulty == 0:
            return f'{label} (авто)'
        return label

    def get_sample_task(self):
        """Возвращает одно задание из группы для предварительного просмотра"""
        return self.taskgroup_set.first().task if self.taskgroup_set.exists() else None


class TaskGroup(BaseModel):
    """Промежуточная модель для связи заданий и групп"""
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, verbose_name='Задание')
    group = models.ForeignKey(AnalogGroup, on_delete=models.CASCADE, verbose_name='Группа')
    bank_role = models.CharField(
        'Роль задания в банке',
        max_length=20,
        choices=TASK_BANK_ROLE_SPECIFIC_CHOICES,
        default=TASK_BANK_ROLE_CONTROL,
        db_index=True,
    )
    
    class Meta:
        verbose_name = 'Задание в группе'
        verbose_name_plural = 'Задания в группах'
        unique_together = ['task', 'group']
    
    def __str__(self):
        return f"{self.task.topic} в {self.group.name} ({self.get_bank_role_display()})"
