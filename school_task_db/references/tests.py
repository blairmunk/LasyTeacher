from django import forms
from django.test import TestCase

from references.admin import SubjectReferenceAdminForm
from references.models import SimpleReference


class SubjectReferenceAdminFormTests(TestCase):
    def test_uses_active_subject_reference_as_select_choices(self):
        SimpleReference.objects.create(
            category='subjects',
            items_text='Физика\nМатематика',
            is_active=True,
        )

        form = SubjectReferenceAdminForm()

        self.assertIsInstance(form.fields['subject'], forms.ChoiceField)
        self.assertEqual(
            list(form.fields['subject'].choices),
            [
                ('', '--- Выберите ---'),
                ('Физика', 'Физика'),
                ('Математика', 'Математика'),
            ],
        )
