from io import StringIO

from django import forms
from django.core.management import call_command
from django.test import TestCase

from references.admin import SubjectReferenceAdminForm
from references.models import SimpleReference, SubjectReference


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


class InitSimpleReferencesCommandTests(TestCase):
    def test_creates_seed_with_subject_names_used_by_application(self):
        output = StringIO()

        call_command('init_simple_references', stdout=output)

        self.assertEqual(SimpleReference.objects.count(), 6)
        self.assertEqual(SubjectReference.objects.count(), 6)
        self.assertTrue(SubjectReference.objects.filter(
            subject='Физика',
            category='content_elements',
        ).exists())
        self.assertFalse(SubjectReference.objects.filter(
            subject='physics',
        ).exists())
        self.assertIn('Создано: 12', output.getvalue())

    def test_repeat_skips_and_force_updates_without_replacing_row(self):
        call_command('init_simple_references', stdout=StringIO())
        reference = SimpleReference.objects.get(category='subjects')
        original_pk = reference.pk
        reference.items_text = 'Изменено'
        reference.save()
        repeat_output = StringIO()

        call_command('init_simple_references', stdout=repeat_output)

        self.assertEqual(
            SimpleReference.objects.get(category='subjects').items_text,
            'Изменено',
        )
        self.assertIn('без изменений: 12', repeat_output.getvalue())

        force_output = StringIO()
        call_command(
            'init_simple_references',
            '--force',
            stdout=force_output,
        )

        refreshed = SimpleReference.objects.get(category='subjects')
        self.assertEqual(refreshed.pk, original_pk)
        self.assertIn('Физика', refreshed.items_text)
        self.assertIn('обновлено: 12', force_output.getvalue())
