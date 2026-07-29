from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from core_logic.entities.document import PrintSettingsSpec
from document_engine.models import PrintSettings


class PrintSettingsModelTests(TestCase):
    def test_converts_model_to_presentation_spec(self):
        user = User.objects.create_user(username='teacher')
        profile = PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
            created_by=user,
            html_template_override='<html>{{ body_content }}</html>',
            latex_template_override='\\begin{document}{{ body_content }}',
            custom_css='body { font-size: 14px; }',
            custom_latex_preamble='\\usepackage{multicol}',
        )

        spec = profile.to_print_settings_spec()

        self.assertIsInstance(spec, PrintSettingsSpec)
        self.assertEqual(spec.name, 'Рабочий лист')
        self.assertEqual(spec.print_settings_id, str(profile.pk))
        self.assertEqual(spec.document_type, 'worksheet')
        self.assertTrue(spec.presentation.has_customization)
        self.assertEqual(
            spec.presentation.html_template_override,
            '<html>{{ body_content }}</html>',
        )
        self.assertEqual(
            spec.presentation.latex_template_override,
            '\\begin{document}{{ body_content }}',
        )
        self.assertEqual(spec.presentation.custom_css, 'body { font-size: 14px; }')
        self.assertEqual(
            spec.presentation.custom_latex_preamble,
            '\\usepackage{multicol}',
        )

    def test_string_representation_contains_name_and_type(self):
        profile = PrintSettings(
            name='Ключ',
            document_type=PrintSettings.DocumentType.ANSWER_KEY,
        )

        self.assertEqual(str(profile), 'Ключ (Ключ для проверки)')

    def test_full_clean_accepts_supported_document_type(self):
        profile = PrintSettings(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        profile.full_clean()

    def test_full_clean_rejects_unknown_document_type(self):
        profile = PrintSettings(
            name='Сломанный профиль',
            document_type='unknown_document_type',
        )

        with self.assertRaises(ValidationError) as context:
            profile.full_clean()

        self.assertIn('document_type', context.exception.error_dict)
