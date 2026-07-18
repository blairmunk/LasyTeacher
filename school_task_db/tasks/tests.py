import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from curriculum.models import SubTopic, Topic
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Source, Task
from works.models import Variant, VariantTask, Work


class TaskBulkGroupAjaxTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Механика',
            subject='Физика',
            section='Кинематика',
            grade_level=9,
        )
        self.first_task = Task.objects.create(
            text='Первое задание',
            answer='1',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        self.second_task = Task.objects.create(
            text='Второе задание',
            answer='2',
            topic=self.topic,
            task_type='computational',
            difficulty=3,
        )
        self.group = AnalogGroup.objects.create(name='Существующая группа')
        self.subtopic = SubTopic.objects.create(
            topic=self.topic,
            name='Равноускоренное движение',
            order=1,
        )

    def post_json(self, url_name, payload):
        return self.client.post(
            reverse(f'tasks:{url_name}'),
            data=json.dumps(payload),
            content_type='application/json',
        )

    def task_form_data(self, **overrides):
        data = {
            'text': 'Новое задание',
            'answer': 'Ответ',
            'topic': str(self.topic.pk),
            'subtopic': '',
            'task_type': 'computational',
            'difficulty': '2',
            'cognitive_level': 'understand',
            'content_element': '',
            'requirement_element': '',
            'short_solution': '',
            'full_solution': '',
            'hint': '',
            'instruction': '',
            'estimated_time': '',
            'source': '',
            'source_detail': '',
            'grade': '',
            'year': '',
            'teacher_notes': '',
            'images-TOTAL_FORMS': '0',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '10',
        }
        data.update(overrides)
        return data

    def test_bulk_create_group_creates_group_with_selected_tasks(self):
        response = self.post_json(
            'bulk-create-group',
            {
                'task_ids': [str(self.first_task.pk), str(self.second_task.pk)],
                'group_name': 'Новая группа',
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        group = AnalogGroup.objects.get(pk=data['group_id'])

        self.assertTrue(data['success'])
        self.assertEqual(data['added'], 2)
        self.assertEqual(group.name, 'Новая группа')
        self.assertEqual(
            TaskGroup.objects.filter(group=group).count(),
            2,
        )

    def test_bulk_add_to_group_adds_only_new_memberships(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)

        response = self.post_json(
            'bulk-add-to-group',
            {
                'task_ids': [str(self.first_task.pk), str(self.second_task.pk)],
                'group_id': str(self.group.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['added'], 1)
        self.assertEqual(data['skipped'], 1)
        self.assertEqual(
            TaskGroup.objects.filter(group=self.group).count(),
            2,
        )

    def test_bulk_remove_from_groups_removes_selected_task_memberships(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)
        TaskGroup.objects.create(task=self.second_task, group=self.group)

        response = self.post_json(
            'bulk-remove-from-groups',
            {'task_ids': [str(self.first_task.pk)]},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['removed'], 1)
        self.assertFalse(
            TaskGroup.objects.filter(task=self.first_task, group=self.group).exists()
        )
        self.assertTrue(
            TaskGroup.objects.filter(task=self.second_task, group=self.group).exists()
        )

    def test_bulk_create_work_creates_work_with_first_variant(self):
        response = self.post_json(
            'bulk-create-work',
            {
                'task_ids': [str(self.second_task.pk), str(self.first_task.pk)],
                'work_name': '  Проверочная  ',
                'work_type': 'quiz',
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        work = Work.objects.get(pk=data['work_id'])
        variant = Variant.objects.get(pk=data['variant_id'])
        variant_tasks = list(
            VariantTask.objects.filter(variant=variant).order_by('order')
        )

        self.assertTrue(data['success'])
        self.assertEqual(data['tasks_count'], 2)
        self.assertEqual(data['redirect_url'], f'/works/{work.pk}/')
        self.assertEqual(work.name, 'Проверочная')
        self.assertEqual(work.work_type, 'quiz')
        self.assertEqual(work.variant_counter, 1)
        self.assertEqual(variant.work, work)
        self.assertEqual(
            [variant_task.task for variant_task in variant_tasks],
            [self.second_task, self.first_task],
        )

    def test_task_list_uses_filters_and_context_data(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)

        response = self.client.get(
            reverse('tasks:list'),
            {
                'search': 'Первое',
                'topic': str(self.topic.pk),
                'group_filter': 'has_group',
                'analog_group': str(self.group.pk),
                'verified': '0',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['tasks'][0].pk, str(self.first_task.pk))
        self.assertEqual(response.context['tasks'][0].text, self.first_task.text)
        self.assertEqual(response.context['tasks'][0].topic_name, self.topic.name)
        self.assertEqual(response.context['tasks'][0].group_count, 1)
        self.assertEqual(response.context['total_tasks'], 2)
        self.assertEqual(response.context['ungrouped_count'], 1)
        self.assertIn(self.group, list(response.context['analog_groups']))
        self.assertEqual(response.context['current_topic'], str(self.topic.pk))
        self.assertEqual(response.context['current_group_filter'], 'has_group')

    def test_task_detail_uses_group_context(self):
        TaskGroup.objects.create(task=self.first_task, group=self.group)

        response = self.client.get(
            reverse('tasks:detail', kwargs={'pk': self.first_task.pk}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['task'].pk, str(self.first_task.pk))
        self.assertEqual(response.context['task'].text, self.first_task.text)
        self.assertEqual(response.context['task_groups'][0].pk, str(self.group.pk))
        self.assertEqual(response.context['task_groups'][0].name, self.group.name)

    def test_task_detail_returns_404_for_missing_task(self):
        response = self.client.get(
            reverse(
                'tasks:detail',
                kwargs={'pk': '550e8400-e29b-41d4-a716-446655440000'},
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_load_subtopics_returns_topic_options(self):
        response = self.client.get(
            reverse('tasks:ajax-load-subtopics'),
            {'topic_id': str(self.topic.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'subtopics': [
                    {'id': str(self.subtopic.pk), 'name': self.subtopic.name},
                ],
            },
        )

    def test_load_subtopics_returns_empty_for_missing_topic(self):
        response = self.client.get(
            reverse('tasks:ajax-load-subtopics'),
            {'topic_id': '00000000-0000-0000-0000-000000000000'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'subtopics': []})

    def test_source_list_returns_sources_with_task_count(self):
        source = Source.objects.create(name='Задачник')
        self.first_task.source = source
        self.first_task.save()

        response = self.client.get(reverse('tasks:source-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sources'][0].pk, str(source.pk))
        self.assertEqual(response.context['sources'][0].name, source.name)
        self.assertEqual(response.context['sources'][0].task_count, 1)

    def test_refresh_math_cache_forbids_non_staff(self):
        response = self.client.get(reverse('tasks:refresh_math_cache'))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'error': 'Доступ запрещен'})

    def test_refresh_math_cache_returns_stats_for_staff(self):
        staff = User.objects.create_user(
            username='staff',
            password='pass',
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse('tasks:refresh_math_cache'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Кэш успешно обновлен')
        self.assertIn('with_math', data['stats'])

    def test_create_task_saves_task_with_empty_image_formset(self):
        response = self.client.post(
            reverse('tasks:create'),
            data=self.task_form_data(text='Созданное задание'),
        )

        created_task = Task.objects.get(text='Созданное задание')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('tasks:detail', kwargs={'pk': created_task.pk}),
        )
        self.assertEqual(created_task.topic, self.topic)

    def test_update_task_saves_task_with_empty_image_formset(self):
        response = self.client.post(
            reverse('tasks:update', kwargs={'pk': self.first_task.pk}),
            data=self.task_form_data(
                text='Обновлённое задание',
                answer=self.first_task.answer,
                difficulty=str(self.first_task.difficulty),
            ),
        )

        self.first_task.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('tasks:detail', kwargs={'pk': self.first_task.pk}),
        )
        self.assertEqual(self.first_task.text, 'Обновлённое задание')

    def test_delete_task_removes_task(self):
        task_id = self.first_task.pk

        response = self.client.post(
            reverse('tasks:delete', kwargs={'pk': task_id}),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tasks:list'))
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

    def test_delete_task_confirmation_uses_explicit_cancel_url(self):
        response = self.client.get(
            reverse('tasks:delete', kwargs={'pk': self.first_task.pk}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['cancel_url'],
            reverse('tasks:detail', kwargs={'pk': self.first_task.pk}),
        )

    def test_create_source_saves_source(self):
        response = self.client.post(
            reverse('tasks:source-create'),
            data={
                'name': 'Новый источник',
                'short_name': 'НИ',
                'source_type': 'problem_book',
                'author': '',
                'year': '',
                'url': '',
                'isbn': '',
                'notes': '',
            },
        )

        source = Source.objects.get(name='Новый источник')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tasks:source-list'))
        self.assertEqual(source.short_name, 'НИ')
