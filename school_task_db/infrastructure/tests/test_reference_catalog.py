from django.test import TestCase

from infrastructure.repositories.django_task_taxonomy_repo import (
    DjangoTaskTaxonomyRepository,
)
from tasks.models import Task


class DjangoReferenceCatalogTests(TestCase):
    def test_task_type_options_use_codes_accepted_by_task_model(self):
        options = DjangoTaskTaxonomyRepository().get_task_type_choices()

        self.assertEqual(options, tuple(Task.TASK_TYPES))
        self.assertIn(('computational', 'Расчётная задача'), options)
