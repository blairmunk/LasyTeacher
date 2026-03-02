from django.db import models
from django.urls import reverse
from core.models import BaseModel
import random


class Work(BaseModel):
    """Работа"""
    WORK_TYPE_CHOICES = [
        ('test', 'Контрольная работа'),
        ('quiz', 'Самостоятельная работа'),
        ('exam', 'Экзамен'),
        ('diagnostic', 'Диагностическая работа'),
        ('homework', 'Домашняя работа'),
        ('practice', 'Практическая работа'),
    ]

    name = models.CharField('Название работы', max_length=200)
    duration = models.PositiveIntegerField('Время выполнения (минуты)', default=45)
    variant_counter = models.PositiveIntegerField('Счётчик вариантов', default=0)
    work_type = models.CharField('Тип работы', max_length=50,
                                 choices=WORK_TYPE_CHOICES, default='test')

    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"

    def get_absolute_url(self):
        return reverse('works:detail', kwargs={'pk': self.pk})

    def generate_variants(self, count=1):
        """Генерация вариантов с заполнением weight"""
        variants = []
        for i in range(count):
            self.variant_counter += 1
            variant = Variant.objects.create(
                work=self,
                number=self.variant_counter
            )

            task_order = 1
            for work_group in self.workanaloggroup_set.order_by('order', 'pk'):
                from task_groups.models import TaskGroup
                available_task_groups = TaskGroup.objects.filter(
                    group=work_group.analog_group
                )
                available_tasks = [tg.task for tg in available_task_groups]

                if len(available_tasks) >= work_group.count:
                    selected_tasks = random.sample(available_tasks, work_group.count)
                else:
                    selected_tasks = available_tasks

                for task in selected_tasks:
                    VariantTask.objects.create(
                        variant=variant,
                        task=task,
                        order=task_order,
                        weight=task.difficulty or 1
                    )
                    task_order += 1

            variants.append(variant)

        self.save()
        return variants

    def sync_analog_groups_from_variants(self):
        """Анализирует варианты и создаёт WorkAnalogGroup автоматически.
        
        Логика: смотрим задания каждого варианта, находим в каких AnalogGroup
        они состоят, и создаём спецификацию работы.
        Возвращает количество созданных групп.
        """
        from task_groups.models import TaskGroup, AnalogGroup

        # Собираем: для каждого варианта, какие группы и сколько заданий
        group_max_counts = {}  # {analog_group_id: max_count_across_variants}

        for variant in self.variant_set.all():
            variant_tasks = list(variant.tasks.all())
            group_counts = {}  # {analog_group_id: count} для этого варианта

            for task in variant_tasks:
                task_group_links = TaskGroup.objects.filter(
                    task=task
                ).select_related('group')
                for tgl in task_group_links:
                    gid = tgl.group_id
                    group_counts[gid] = group_counts.get(gid, 0) + 1

            for gid, count in group_counts.items():
                group_max_counts[gid] = max(
                    group_max_counts.get(gid, 0), count
                )

        if not group_max_counts:
            return 0

        # Создаём/обновляем WorkAnalogGroup
        created = 0
        for order, (gid, count) in enumerate(group_max_counts.items(), 1):
            _, was_created = WorkAnalogGroup.objects.update_or_create(
                work=self,
                analog_group_id=gid,
                defaults={'count': count, 'order': order}
            )
            if was_created:
                created += 1

        return created

    @property
    def max_points(self):
        """Максимальный балл работы (сумма difficulty из первого варианта)"""
        first_variant = self.variant_set.first()
        if first_variant:
            return sum(t.difficulty or 0 for t in first_variant.tasks.all())
        return 0


class WorkAnalogGroup(BaseModel):
    """Связь работы с группой аналогов: спецификация работы"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    analog_group = models.ForeignKey('task_groups.AnalogGroup',
                                     on_delete=models.CASCADE,
                                     verbose_name='Группа аналогов')
    count = models.PositiveIntegerField('Количество заданий', default=1)
    order = models.PositiveIntegerField('Порядок в работе', default=0,
                                        help_text='Порядок следования задания в работе')

    class Meta:
        verbose_name = 'Группа заданий в работе'
        verbose_name_plural = 'Группы заданий в работе'
        unique_together = ['work', 'analog_group']
        ordering = ['order', 'pk']

    def __str__(self):
        return f"{self.work.name} — #{self.order} {self.analog_group.name} (×{self.count})"


class Variant(BaseModel):
    """Вариант работы — конкретный набор заданий"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    number = models.PositiveIntegerField('Номер варианта')
    tasks = models.ManyToManyField('tasks.Task', through='VariantTask',
                                   verbose_name='Задания')

    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'
        ordering = ['work', 'number']
        unique_together = ['work', 'number']

    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.work.name} - Вариант {self.number}"

    def get_absolute_url(self):
        return reverse('works:variant-detail', kwargs={'pk': self.pk})

    def ordered_tasks(self):
        """Задания варианта в правильном порядке"""
        return self.tasks.order_by('varianttask__order')


class VariantTask(BaseModel):
    """Задание в варианте с порядковым номером и весом"""
    variant = models.ForeignKey(
        Variant, 
        on_delete=models.CASCADE,
        verbose_name='Вариант'
    )
    task = models.ForeignKey(
        'tasks.Task', 
        on_delete=models.CASCADE,
        verbose_name='Задание'
    )
    order = models.PositiveIntegerField(
        'Номер задания в варианте', 
        default=0
    )
    weight = models.PositiveIntegerField(
        'Вес задания',
        default=1,
        help_text='Вес для нормировки баллов. По умолчанию = difficulty задачи'
    )
    
    class Meta:
        verbose_name = 'Задание в варианте'
        verbose_name_plural = 'Задания в варианте'
        ordering = ['order']
        unique_together = ['variant', 'task']
    
    def __str__(self):
        return f"Вариант {self.variant.number} — #{self.order} {self.task} (вес={self.weight})"
    
    def get_max_points(self, scale='primary'):
        """Расчёт макс. балла по шкале"""
        if scale == 'primary':
            return self.weight
        else:  # 100-балльная
            total_weight = self.variant.varianttask_set.aggregate(
                models.Sum('weight')
            )['weight__sum']
            return round((self.weight / total_weight) * 100, 1)
