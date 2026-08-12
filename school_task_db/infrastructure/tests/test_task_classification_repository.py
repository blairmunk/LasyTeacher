from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry, Requirement
from core_logic.entities.task import TaskSaveParams
from curriculum.models import Topic
from infrastructure.container import Container
from infrastructure.forms.task_django_forms import TaskForm
from infrastructure.repositories.django_task_export_repo import (
    DjangoTaskExportRepository,
)
from infrastructure.repositories.django_task_read_repo import (
    DjangoTaskReadRepository,
)
from infrastructure.repositories.django_task_classification_repo import (
    DjangoTaskClassificationRepository,
)
from tasks.models import Task
from core_logic.entities.task import TaskExportFilters


class DjangoTaskClassificationRepositoryTests(TestCase):
    def setUp(self):
        self.physics_topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.chemistry_topic = Topic.objects.create(
            name='Атомы',
            subject='Химия',
            section='Строение вещества',
            grade_level=8,
        )
        physics = CodifierSpec.objects.create(
            name='ОГЭ по физике 2026',
            short_name='ОГЭ Физика',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        chemistry = CodifierSpec.objects.create(
            name='ОГЭ по химии 2026',
            short_name='ОГЭ Химия',
            subject='Химия',
            exam_type='oge',
            year=2026,
        )
        self.physics_entry = ContentEntry.objects.create(
            codifier=physics,
            code='1.1',
            name='Динамика',
        )
        self.chemistry_entry = ContentEntry.objects.create(
            codifier=chemistry,
            code='1.1',
            name='Строение атома',
        )
        self.physics_requirement = Requirement.objects.create(
            codifier=physics,
            code='2.1',
            name='Решать задачи',
        )
        self.chemistry_requirement = Requirement.objects.create(
            codifier=chemistry,
            code='2.1',
            name='Составлять реакции',
        )

    def test_validation_accepts_same_subject_and_rejects_other_subject(self):
        repo = DjangoTaskClassificationRepository()

        valid = repo.get_classification_errors(
            str(self.physics_topic.pk),
            (str(self.physics_entry.pk),),
            (str(self.physics_requirement.pk),),
        )
        invalid = repo.get_classification_errors(
            str(self.physics_topic.pk),
            (str(self.chemistry_entry.pk),),
            (str(self.chemistry_requirement.pk),),
        )

        self.assertEqual(valid, ())
        self.assertEqual(len(invalid), 2)
        self.assertIn('другого предмета', invalid[0])

    def test_options_include_only_active_codifiers_for_topic_subject(self):
        inactive = CodifierSpec.objects.create(
            name='Старый кодификатор по физике',
            short_name='Физика 2025',
            subject='Физика',
            exam_type='oge',
            year=2025,
            is_active=False,
        )
        ContentEntry.objects.create(
            codifier=inactive,
            code='9.1',
            name='Устаревший элемент',
        )

        options = DjangoTaskClassificationRepository().get_classification_options(
            str(self.physics_topic.pk),
        )

        self.assertEqual(
            [option.id for option in options.content_entries],
            [str(self.physics_entry.pk)],
        )
        self.assertEqual(
            [option.id for option in options.requirements],
            [str(self.physics_requirement.pk)],
        )
        self.assertIn('ОГЭ Физика · 1.1 · Динамика', options.content_entries[0].name)
        self.assertIn('Тр. 2.1', options.requirements[0].name)

    def test_options_are_empty_for_invalid_topic(self):
        options = DjangoTaskClassificationRepository().get_classification_options(
            'invalid-topic-id',
        )

        self.assertEqual(options.content_entries, [])
        self.assertEqual(options.requirements, [])

    def test_use_case_creates_and_updates_explicit_classifications(self):
        container = Container()
        create_result = container.create_task_use_case().execute(
            TaskSaveParams(
                text='Найти силу',
                answer='10 Н',
                topic_id=str(self.physics_topic.pk),
                task_type='computational',
                difficulty=2,
                content_entry_ids=(str(self.physics_entry.pk),),
                requirement_ids=(str(self.physics_requirement.pk),),
            ),
        )

        task = Task.objects.get(pk=create_result.task_id)
        self.assertEqual(
            list(task.codifier_content_entries.all()),
            [self.physics_entry],
        )
        self.assertEqual(
            list(task.codifier_requirements.all()),
            [self.physics_requirement],
        )

        update_result = container.update_task_use_case().execute(
            TaskSaveParams(
                task_id=str(task.pk),
                text=task.text,
                answer=task.answer,
                topic_id=str(self.physics_topic.pk),
                task_type=task.task_type,
                difficulty=task.difficulty,
            ),
        )

        self.assertEqual(update_result.status, 'updated')
        self.assertFalse(task.codifier_content_entries.exists())
        self.assertFalse(task.codifier_requirements.exists())

    def test_bound_form_filters_choices_by_selected_topic_subject(self):
        form = TaskForm(data={
            'topic': str(self.physics_topic.pk),
        })

        self.assertEqual(
            list(form.fields['codifier_content_entries'].queryset),
            [self.physics_entry],
        )
        self.assertEqual(
            list(form.fields['codifier_requirements'].queryset),
            [self.physics_requirement],
        )

    def test_edit_form_preserves_explicit_initial_selection(self):
        task = Task.objects.create(
            text='Найти силу',
            answer='10 Н',
            topic=self.physics_topic,
            task_type='computational',
            difficulty=2,
        )
        self.physics_entry.tasks.add(task)
        self.physics_requirement.tasks.add(task)

        form = TaskForm(instance=task)

        self.assertEqual(
            form.initial['codifier_content_entries'],
            (self.physics_entry.pk,),
        )
        self.assertEqual(
            form.initial['codifier_requirements'],
            (self.physics_requirement.pk,),
        )

    def test_container_wires_classification_repository(self):
        container = Container()

        self.assertIsInstance(
            container.task_classification_repo,
            DjangoTaskClassificationRepository,
        )

    def test_export_repository_uses_portable_natural_keys(self):
        task = Task.objects.create(
            text='Найти силу',
            answer='10 Н',
            topic=self.physics_topic,
            task_type='computational',
            difficulty=2,
        )
        self.physics_entry.tasks.add(task)
        self.physics_requirement.tasks.add(task)

        source = DjangoTaskExportRepository().get_task_export_sources(
            TaskExportFilters(topic_id=str(self.physics_topic.pk)),
        )[0]

        self.assertEqual(source.content_entries[0].subject, 'Физика')
        self.assertEqual(source.content_entries[0].exam_type, 'oge')
        self.assertEqual(source.content_entries[0].year, 2026)
        self.assertEqual(source.content_entries[0].code, '1.1')
        self.assertEqual(source.requirements[0].code, '2.1')

    def test_task_detail_exposes_explicit_classification_labels(self):
        task = Task.objects.create(
            text='Найти силу',
            answer='10 Н',
            topic=self.physics_topic,
            task_type='computational',
            difficulty=2,
        )
        self.physics_entry.tasks.add(task)
        self.physics_requirement.tasks.add(task)

        detail = DjangoTaskReadRepository().get_task(str(task.pk))

        self.assertEqual(detail.content_entries[0].codifier_name, 'ОГЭ Физика')
        self.assertEqual(detail.content_entries[0].code, '1.1')
        self.assertEqual(detail.content_entries[0].name, 'Динамика')
        self.assertEqual(detail.requirements[0].code, '2.1')
