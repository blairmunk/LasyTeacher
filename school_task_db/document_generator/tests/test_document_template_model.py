from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from document_generator.models import DocumentTemplate


class DocumentTemplateModelTests(TestCase):
    def test_converts_model_to_template_spec(self):
        user = User.objects.create_user(username='teacher')
        template = DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            created_by=user,
            sections_config=[
                {
                    'type': 'header',
                    'params': {'show_date': True},
                },
                {
                    'type': 'task_list',
                    'params': {'source': 'new_tasks'},
                },
            ],
            default_content_config={'answer_type': 'tasks_only'},
            html_template_override='<html>{{ body_content }}</html>',
            latex_template_override='\\begin{document}{{ body_content }}',
            custom_css='body { font-size: 14px; }',
            custom_latex_preamble='\\usepackage{multicol}',
        )

        spec = template.to_template_spec()

        self.assertEqual(spec.name, 'Рабочий лист')
        self.assertEqual(spec.template_id, str(template.pk))
        self.assertEqual(spec.template_type, 'worksheet')
        self.assertEqual(spec.section_types, ('header', 'task_list'))
        self.assertEqual(
            spec.sections[1].options,
            {'source': 'new_tasks'},
        )
        self.assertEqual(
            spec.default_content_config,
            {'answer_type': 'tasks_only'},
        )
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
        template = DocumentTemplate(
            name='Ключ',
            template_type=DocumentTemplate.TemplateType.ANSWER_KEY,
        )

        self.assertEqual(str(template), 'Ключ (Ключ для проверки)')

    def test_full_clean_accepts_valid_sections_config(self):
        template = DocumentTemplate(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[
                {
                    'type': 'task_list',
                    'params': {'source': 'new_tasks'},
                },
            ],
        )

        template.full_clean()

    def test_full_clean_rejects_invalid_sections_config(self):
        template = DocumentTemplate(
            name='Сломанный шаблон',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[
                {
                    'type': 'task_list',
                    'params': ['not', 'a', 'mapping'],
                },
            ],
        )

        with self.assertRaises(ValidationError) as context:
            template.full_clean()

        self.assertIn('sections_config', context.exception.error_dict)

    def test_full_clean_rejects_unknown_section_type(self):
        template = DocumentTemplate(
            name='Сломанный шаблон',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[
                {
                    'type': 'unknown_section',
                    'params': {},
                },
            ],
        )

        with self.assertRaises(ValidationError) as context:
            template.full_clean()

        self.assertIn('sections_config', context.exception.error_dict)

    def test_full_clean_rejects_unknown_template_type(self):
        template = DocumentTemplate(
            name='Сломанный шаблон',
            template_type='unknown_document_type',
            sections_config=[],
        )

        with self.assertRaises(ValidationError) as context:
            template.full_clean()

        self.assertIn('template_type', context.exception.error_dict)
        self.assertIn('sections_config', context.exception.error_dict)

    def test_full_clean_rejects_section_for_wrong_template_type(self):
        template = DocumentTemplate(
            name='Сломанный шаблон',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[
                {
                    'type': 'original_mistakes',
                    'params': {},
                },
            ],
        )

        with self.assertRaises(ValidationError) as context:
            template.full_clean()

        self.assertIn('sections_config', context.exception.error_dict)
