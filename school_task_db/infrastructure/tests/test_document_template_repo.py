from django.test import TestCase

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    UpdateDocumentTemplateParams,
)
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

    def test_returns_template_spec_by_id_and_type(self):
        template_model = DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )

        template = DjangoDocumentTemplateRepository().get_template_spec(
            template_id=str(template_model.pk),
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
        )

        self.assertEqual(template.template_id, str(template_model.pk))
        self.assertEqual(template.name, 'Рабочий лист')

    def test_returns_none_when_template_id_has_wrong_type(self):
        template_model = DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )

        template = DjangoDocumentTemplateRepository().get_template_spec(
            template_id=str(template_model.pk),
            template_type=DocumentTemplate.TemplateType.ANSWER_KEY,
        )

        self.assertIsNone(template)

    def test_creates_template_from_clean_params(self):
        template_id = DjangoDocumentTemplateRepository().create_template(
            CreateDocumentTemplateParams(
                name='Шаблон работы',
                description='Для печати',
                template_type=DocumentTemplate.TemplateType.WORK,
                section_types=('header', 'task_list'),
                is_default=True,
            )
        )

        template = DocumentTemplate.objects.get(pk=template_id)
        self.assertEqual(template.name, 'Шаблон работы')
        self.assertEqual(template.description, 'Для печати')
        self.assertEqual(template.template_type, DocumentTemplate.TemplateType.WORK)
        self.assertEqual(
            template.sections_config,
            [{'type': 'header'}, {'type': 'task_list'}],
        )
        self.assertTrue(template.is_default)

    def test_creating_default_template_clears_previous_default_for_type(self):
        old_default = DocumentTemplate.objects.create(
            name='Старый шаблон',
            template_type=DocumentTemplate.TemplateType.WORK,
            sections_config=[{'type': 'header'}],
            is_default=True,
        )

        DjangoDocumentTemplateRepository().create_template(
            CreateDocumentTemplateParams(
                name='Новый шаблон',
                template_type=DocumentTemplate.TemplateType.WORK,
                section_types=('header', 'task_list'),
                is_default=True,
            )
        )

        old_default.refresh_from_db()
        self.assertFalse(old_default.is_default)

    def test_updates_template_from_clean_params(self):
        template = DocumentTemplate.objects.create(
            name='Старый шаблон',
            template_type=DocumentTemplate.TemplateType.WORK,
            sections_config=[{'type': 'header'}],
        )

        updated = DjangoDocumentTemplateRepository().update_template(
            UpdateDocumentTemplateParams(
                template_id=str(template.pk),
                name='Новый шаблон',
                description='Новое описание',
                template_type=DocumentTemplate.TemplateType.WORK,
                section_types=('header', 'task_list'),
                is_default=True,
            )
        )

        template.refresh_from_db()
        self.assertTrue(updated)
        self.assertEqual(template.name, 'Новый шаблон')
        self.assertEqual(template.description, 'Новое описание')
        self.assertEqual(
            template.sections_config,
            [{'type': 'header'}, {'type': 'task_list'}],
        )
        self.assertTrue(template.is_default)

    def test_update_returns_false_for_missing_template(self):
        updated = DjangoDocumentTemplateRepository().update_template(
            UpdateDocumentTemplateParams(
                template_id='550e8400-e29b-41d4-a716-446655440000',
                name='Шаблон',
                template_type=DocumentTemplate.TemplateType.WORK,
                section_types=('header',),
            )
        )

        self.assertFalse(updated)
