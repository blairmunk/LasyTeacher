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
