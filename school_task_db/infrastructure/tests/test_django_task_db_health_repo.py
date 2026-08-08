from django.test import TestCase

from curriculum.models import Course, Topic
from infrastructure.repositories.django_task_db_health_repo import (
    DjangoTaskDBHealthRepository,
)
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, Work, WorkAnalogGroup


class DjangoTaskDBHealthRepositoryTests(TestCase):
    def test_returns_task_database_health_facts(self):
        topic = Topic.objects.create(
            name='Скорость',
            subject='Физика',
            section='Кинематика',
            grade_level=7,
        )
        task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
            is_verified=False,
            grade=None,
        )
        empty_group = AnalogGroup.objects.create(name='Пустая группа')
        fragile_group = AnalogGroup.objects.create(name='Хрупкая группа')
        TaskGroup.objects.create(task=task, group=fragile_group)
        work_no_spec = Work.objects.create(name='Без спецификации')
        spec_work = Work.objects.create(name='Со спецификацией')
        WorkAnalogGroup.objects.create(
            work=spec_work,
            analog_group=fragile_group,
            count=2,
        )
        orphan_variant = Variant.objects.create(work=None, number=1)
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )

        data = DjangoTaskDBHealthRepository().get_task_db_health_source()

        self.assertEqual(data.total_tasks, 1)
        self.assertEqual(len(data.group_sizes), 2)
        self.assertEqual(data.total_works, 2)
        self.assertEqual(data.total_variants, 1)
        self.assertEqual(data.orphan_variants_count, 1)
        self.assertEqual(data.orphan_variant_samples[0].number, 1)
        self.assertEqual(
            data.orphan_variant_samples[0].short_uuid,
            orphan_variant.get_short_uuid(),
        )
        groups_by_id = {item.group.pk: item for item in data.group_sizes}
        self.assertEqual(groups_by_id[str(empty_group.pk)].task_count, 0)
        self.assertEqual(groups_by_id[str(fragile_group.pk)].task_count, 1)
        self.assertEqual(data.coverage[0].work.pk, str(spec_work.pk))
        self.assertEqual(data.coverage[0].group.pk, str(fragile_group.pk))
        self.assertEqual(data.coverage[0].needed, 2)
        self.assertEqual(data.coverage[0].available, 1)
        self.assertEqual(data.ungrouped_tasks_count, 0)
        self.assertEqual(data.works_no_variants_count, 2)
        self.assertEqual(data.works_no_spec_samples[0].pk, str(work_no_spec.pk))
        self.assertEqual(data.difficulty_counts[0].key, 2)
        self.assertEqual(data.type_counts[0].key, 'computational')
        self.assertEqual(data.unverified_tasks_count, 1)
        self.assertEqual(data.no_source_tasks_count, 1)
        self.assertEqual(data.no_grade_tasks_count, 1)
        self.assertEqual(data.courses[0].pk, str(course.pk))
