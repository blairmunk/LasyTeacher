from django.db import models
from django.urls import reverse
from core.models import BaseModel
import random

class Work(BaseModel):
    """Работа"""
    name = models.CharField('Название работы', max_length=200)
    duration = models.PositiveIntegerField('Время выполнения (минуты)', default=45)
    variant_counter = models.PositiveIntegerField('Счётчик вариантов', default=0)
    
    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('works:detail', kwargs={'pk': self.pk})
    
    def generate_variants(self, count=1):
        """Генерация вариантов на основе работы"""
        variants = []
        for i in range(count):
            self.variant_counter += 1
            variant = Variant.objects.create(
                work=self,
                number=self.variant_counter
            )
            
            # Добавляем задания в вариант
            for work_group in self.workanaloggroup_set.all():
                # Получаем случайные задания из группы
                from task_groups.models import TaskGroup
                available_task_groups = TaskGroup.objects.filter(group=work_group.analog_group)
                available_tasks = [tg.task for tg in available_task_groups]
                
                if len(available_tasks) >= work_group.count:
                    selected_tasks = random.sample(available_tasks, work_group.count)
                    variant.tasks.add(*selected_tasks)
            
            variants.append(variant)
        
        self.save()
        return variants

class WorkAnalogGroup(BaseModel):
    """Связь работы с группой аналогов и количеством заданий"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    analog_group = models.ForeignKey('task_groups.AnalogGroup', on_delete=models.CASCADE, verbose_name='Группа аналогов')
    count = models.PositiveIntegerField('Количество заданий', default=1)
    
    class Meta:
        verbose_name = 'Группа заданий в работе'
        verbose_name_plural = 'Группы заданий в работе'
        unique_together = ['work', 'analog_group']
    
    def __str__(self):
        return f"{self.work.name} - {self.analog_group.name} ({self.count})"

class Variant(BaseModel):
    """Вариант работы"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    number = models.PositiveIntegerField('Номер варианта')
    tasks = models.ManyToManyField('tasks.Task', verbose_name='Задания')
    
    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'
        ordering = ['work', 'number']
        unique_together = ['work', 'number']
    
    def __str__(self):
        return f"{self.work.name} - Вариант {self.number}"
    
    def get_absolute_url(self):
        return reverse('works:variant-detail', kwargs={'pk': self.pk})
