from django.db import models
from django.urls import reverse
from core.models import BaseModel
import random


class Work(BaseModel):
    """Работа — мутабельный шаблон"""
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
    max_score = models.PositiveIntegerField(
        'Максимальный балл', default=0,
        help_text='Шкала нормировки. 0 = сумма весов (без нормировки)'
    )
    @property
    def effective_max_score(self):
        """Эффективный макс. балл: если max_score=0, считаем сумму весов"""
        if self.max_score:
            return self.max_score
        return sum(
            wg.weight * wg.count
            for wg in self.workanaloggroup_set.all()
        )


    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"

    def get_absolute_url(self):
        return reverse('works:detail', kwargs={'pk': self.pk})

    def _calc_points_distribution(self):
        """Рассчитать распределение баллов по спецификации.
        Если max_score=0 — баллы = вес напрямую (без нормировки).
        Иначе — нормировка пропорционально к max_score.
        """
        work_groups = list(self.workanaloggroup_set.order_by('order', 'pk'))
        if not work_groups:
            return []

        # Расширяем: каждый слот задания = вес группы
        task_slots = []
        for wg in work_groups:
            for _ in range(wg.count):
                task_slots.append((wg.weight, wg))

        total_weight = sum(w for w, _ in task_slots)

        # Если max_score=0 — без нормировки, баллы = вес напрямую
        if not self.max_score:
            return [(w, wg) for w, wg in task_slots]

        scale = self.max_score

        if total_weight <= 0:
            return [(0, wg) for _, wg in task_slots]

        # Пропорциональное распределение с корректным округлением
        raw = [w / total_weight * scale for w, _ in task_slots]
        floors = [int(p) for p in raw]
        remainder = scale - sum(floors)

        fracs = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
        for i in range(remainder):
            floors[fracs[i]] += 1

        return [(floors[i], task_slots[i][1]) for i in range(len(task_slots))]


    def get_spec_preview(self):
        """Превью баллов для UI: [{wg, per_task, total_points}, ...]"""
        distribution = self._calc_points_distribution()
        if not distribution:
            return []

        from collections import OrderedDict
        groups = OrderedDict()
        for points, wg in distribution:
            if wg.pk not in groups:
                groups[wg.pk] = {'wg': wg, 'per_task': points, 'total_points': 0}
            groups[wg.pk]['total_points'] += points

        return list(groups.values())

    def generate_variants(self, count=1):
        """Генерация вариантов: баллы рассчитываются из спецификации"""
        variants = []
        distribution = self._calc_points_distribution()
        work_groups = list(self.workanaloggroup_set.order_by('order', 'pk'))

        for i in range(count):
            self.variant_counter += 1
            variant = Variant.objects.create(
                work=self,
                number=self.variant_counter,
                work_name_snapshot=self.name,
                max_score_snapshot=self.effective_max_score,
                duration_snapshot=self.duration,
            )


            task_idx = 0
            task_order = 1
            for work_group in work_groups:
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
                    max_pts = distribution[task_idx][0] if task_idx < len(distribution) else 0
                    VariantTask.objects.create(
                        variant=variant,
                        task=task,
                        order=task_order,
                        max_points=max_pts,
                        weight=work_group.weight,  # deprecated, для обратной совместимости
                    )
                    task_order += 1
                    task_idx += 1

            variants.append(variant)

        self.save()
        return variants

    def sync_analog_groups_from_variants(self):
        """Анализирует варианты и создаёт WorkAnalogGroup автоматически."""
        from task_groups.models import TaskGroup, AnalogGroup

        group_max_counts = {}

        for variant in self.variant_set.all():
            variant_tasks = list(variant.tasks.all())
            group_counts = {}

            for task in variant_tasks:
                task_group_links = TaskGroup.objects.filter(
                    task=task
                ).select_related('group')
                for tgl in task_group_links:
                    gid = tgl.group_id
                    group_counts[gid] = group_counts.get(gid, 0) + 1

            for gid, cnt in group_counts.items():
                group_max_counts[gid] = max(group_max_counts.get(gid, 0), cnt)

        if not group_max_counts:
            return 0

        created = 0
        for order, (gid, cnt) in enumerate(group_max_counts.items(), 1):
            _, was_created = WorkAnalogGroup.objects.update_or_create(
                work=self,
                analog_group_id=gid,
                defaults={'count': cnt, 'order': order}
            )
            if was_created:
                created += 1

        return created


class WorkAnalogGroup(BaseModel):
    """Спецификация работы: группа аналогов + количество + вес"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    analog_group = models.ForeignKey('task_groups.AnalogGroup',
                                     on_delete=models.CASCADE,
                                     verbose_name='Группа аналогов')
    count = models.PositiveIntegerField('Количество заданий', default=1)
    order = models.PositiveIntegerField('Порядок в работе', default=0)
    weight = models.PositiveIntegerField('Вес задания', default=1,
                                          help_text='Вес для нормировки баллов')

    class Meta:
        verbose_name = 'Группа заданий в работе'
        verbose_name_plural = 'Группы заданий в работе'
        unique_together = ['work', 'analog_group']
        ordering = ['order', 'pk']

    def __str__(self):
        return f"{self.work.name} — #{self.order} {self.analog_group.name} (×{self.count}, вес={self.weight})"


class Variant(BaseModel):
    """Вариант работы — иммутабельный набор заданий с баллами"""
    work = models.ForeignKey(Work, on_delete=models.SET_NULL,
                             null=True, blank=True, verbose_name='Работа')
    number = models.PositiveIntegerField('Номер варианта')
    tasks = models.ManyToManyField('tasks.Task', through='VariantTask',
                                   verbose_name='Задания')

    # Снимки данных работы на момент генерации
    work_name_snapshot = models.CharField('Название работы (снимок)',
                                          max_length=200, blank=True, default='')
    max_score_snapshot = models.PositiveIntegerField('Макс. балл (снимок)', default=100)
    duration_snapshot = models.PositiveIntegerField('Время (снимок)', default=45)

    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'
        ordering = ['number']

    def __str__(self):
        name = self.work.name if self.work else self.work_name_snapshot
        return f"[{self.get_short_uuid()}] {name} - Вариант {self.number}"

    def get_absolute_url(self):
        return reverse('works:variant-detail', kwargs={'pk': self.pk})

    @property
    def display_name(self):
        if self.work:
            return self.work.name
        return self.work_name_snapshot or "Удалённая работа"

    @property
    def display_max_score(self):
        return self.max_score_snapshot

    @property
    def display_duration(self):
        return self.duration_snapshot

    def ordered_tasks(self):
        return self.tasks.order_by('varianttask__order')

    @property
    def total_max_points(self):
        result = self.varianttask_set.aggregate(models.Sum('max_points'))
        return result['max_points__sum'] or 0
    @property
    def is_points_frozen(self):
        """Варианты всегда иммутабельны после генерации"""
        return True



class VariantTask(BaseModel):
    """Задание в варианте — иммутабельная запись с баллами"""
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, verbose_name='Вариант')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, verbose_name='Задание')
    order = models.PositiveIntegerField('Номер задания', default=0)
    max_points = models.PositiveIntegerField('Макс. баллов', default=0,
                                              help_text='Рассчитано при генерации из спецификации')
    # DEPRECATED: оставлено для обратной совместимости с генераторами
    weight = models.PositiveIntegerField('Вес (deprecated)', default=1)

    class Meta:
        verbose_name = 'Задание в варианте'
        verbose_name_plural = 'Задания в варианте'
        ordering = ['order']
        unique_together = ['variant', 'task']

    def __str__(self):
        return f"Вариант {self.variant.number} — #{self.order} ({self.max_points} балл.)"
