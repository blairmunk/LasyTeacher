from django.test import TestCase
from django.urls import reverse

from document_generator.models import DocumentTemplate


class DocumentTemplateEditorViewTests(TestCase):
    def test_template_editor_shows_catalog_and_saved_templates(self):
        DocumentTemplate.objects.create(
            name='Шаблон работы',
            template_type=DocumentTemplate.TemplateType.WORK,
            sections_config=[{'type': 'header'}],
        )

        response = self.client.get(
            reverse('document_generator:template-editor'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_generator/template_editor.html',
        )
        self.assertContains(response, 'Шаблоны документов')
        self.assertContains(response, 'Контрольная / самостоятельная')
        self.assertContains(response, 'Шаблон работы')
        self.assertContains(response, 'header')
        self.assertContains(response, 'HTML')
        self.assertContains(response, 'PDF')
        self.assertContains(response, 'LaTeX')
        self.assertContains(response, reverse('document_generator:template-create'))

    def test_template_editor_passes_query_filters_to_clean_use_case(self):
        response = self.client.get(
            reverse('document_generator:template-editor'),
            {'type': 'work', 'renderable': '1', 'legacy': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_document_type'], 'work')
        self.assertTrue(response.context['renderable_only'])
        self.assertTrue(response.context['include_legacy_sections'])
        self.assertContains(response, 'value="work" selected')
        self.assertContains(
            response,
            'href="?type=remedial_sheet&amp;renderable=1&amp;legacy=1"',
        )

    def test_template_create_view_shows_section_form(self):
        response = self.client.get(
            reverse('document_generator:template-create'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_generator/template_form.html',
        )
        self.assertContains(response, 'Новый шаблон документа')
        self.assertContains(response, 'name="template_type"')
        self.assertContains(response, 'value="header"')
        self.assertContains(response, 'value="task_list"')

    def test_template_create_view_creates_template(self):
        response = self.client.post(
            reverse('document_generator:template-create'),
            {
                'name': 'Шаблон работы',
                'description': 'Для печати',
                'template_type': 'work',
                'sections': ['header', 'task_list'],
                'is_default': 'on',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_generator:template-editor'),
        )
        template = DocumentTemplate.objects.get(name='Шаблон работы')
        self.assertEqual(template.description, 'Для печати')
        self.assertEqual(
            template.sections_config,
            [{'type': 'header'}, {'type': 'task_list'}],
        )
        self.assertTrue(template.is_default)

    def test_template_create_view_shows_clean_validation_errors(self):
        response = self.client.post(
            reverse('document_generator:template-create'),
            {
                'name': 'Шаблон РнО',
                'template_type': 'remedial_sheet',
                'sections': ['task_list'],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Section task_list is not supported for document type remedial_sheet',
        )
        self.assertFalse(DocumentTemplate.objects.exists())
