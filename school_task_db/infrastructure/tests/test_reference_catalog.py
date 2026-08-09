from django.test import TestCase

from infrastructure.repositories.django_task_catalog_repo import (
    DjangoTaskCatalogRepository,
)
from references.models import SubjectReference
from tasks.models import Task


class DjangoReferenceCatalogTests(TestCase):
    def test_merges_active_subject_references_across_grade_catalogs(self):
        SubjectReference.objects.create(
            subject='Физика',
            grade_level='7',
            category='content_elements',
            items_text='1.1|Механическое движение\n1.2|Сила',
        )
        SubjectReference.objects.create(
            subject='Физика',
            grade_level='8',
            category='content_elements',
            items_text='1.1|Повтор движения\n2.1|Тепловые явления',
        )
        SubjectReference.objects.create(
            subject='Физика',
            grade_level='9',
            category='content_elements',
            items_text='3.1|Неактивный элемент',
            is_active=False,
        )

        options = DjangoTaskCatalogRepository().get_reference_element_options(
            subject='Физика',
            category='content_elements',
        )

        self.assertEqual(
            [(option.code, option.name) for option in options],
            [
                ('1.1', 'Механическое движение'),
                ('1.2', 'Сила'),
                ('2.1', 'Тепловые явления'),
            ],
        )

    def test_task_type_options_use_codes_accepted_by_task_model(self):
        options = DjangoTaskCatalogRepository().get_task_type_choices()

        self.assertEqual(options, list(Task.TASK_TYPES))
        self.assertIn(('computational', 'Расчётная задача'), options)
