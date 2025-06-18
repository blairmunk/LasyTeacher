from django.db import models
from django.urls import reverse
from core.models import BaseModel

class AnalogGroup(BaseModel):
    """Группа аналогичных заданий"""
    name = models.CharField('Название группы', max_length=200)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Группа аналогичных заданий'
        verbose_name_plural = 'Группы аналогичных заданий'
        ordering = ['name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"
    
    def get_absolute_url(self):
        return reverse('task_groups:detail', kwargs={'pk': self.pk})
    
    def get_sample_task(self):
        """Возвращает одно задание из группы для предварительного просмотра"""
        return self.taskgroup_set.first().task if self.taskgroup_set.exists() else None

class TaskGroup(BaseModel):
    """Промежуточная модель для связи заданий и групп"""
    from tasks.models import Task  # Импорт внутри модели
    
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, verbose_name='Задание')
    group = models.ForeignKey(AnalogGroup, on_delete=models.CASCADE, verbose_name='Группа')
    
    class Meta:
        verbose_name = 'Задание в группе'
        verbose_name_plural = 'Задания в группах'
        unique_together = ['task', 'group']
    
    def __str__(self):
        return f"{self.task.topic} в {self.group.name}"
