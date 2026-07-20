from django.test import TestCase

from document_generator.models import DocumentTemplate
from infrastructure.repositories.django_document_template_repo import (
    DjangoDocumentTemplateRepository,
)


class DjangoDocumentTemplateRepositoryTests(TestCase):
    def test_lists_template_specs_filtered_by_type(self):
        DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )
        DocumentTemplate.objects.create(
            name='Ключ',
            template_type=DocumentTemplate.TemplateType.ANSWER_KEY,
            sections_config=[{'type': 'answers'}],
        )

        templates = DjangoDocumentTemplateRepository().list_template_specs(
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
        )

        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, 'Рабочий лист')
        self.assertEqual(templates[0].template_type, 'worksheet')
        self.assertEqual(templates[0].section_types, ('header',))

    def test_returns_default_template_spec(self):
        DocumentTemplate.objects.create(
            name='Обычный рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            is_default=False,
            sections_config=[{'type': 'header'}],
        )
        DocumentTemplate.objects.create(
            name='Основной рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            is_default=True,
            sections_config=[{'type': 'task_list'}],
        )

        template = DjangoDocumentTemplateRepository().get_default_template_spec(
            DocumentTemplate.TemplateType.WORKSHEET,
        )

        self.assertEqual(template.name, 'Основной рабочий лист')
        self.assertEqual(template.section_types, ('task_list',))

    def test_returns_none_when_default_template_missing(self):
        template = DjangoDocumentTemplateRepository().get_default_template_spec(
            DocumentTemplate.TemplateType.WORKSHEET,
        )

        self.assertIsNone(template)
