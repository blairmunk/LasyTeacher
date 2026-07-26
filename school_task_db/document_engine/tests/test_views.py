from django.test import TestCase
from django.urls import reverse

from document_engine.models import PrintSettings


class PrintSettingsViewTests(TestCase):
    def test_print_settings_editor_shows_catalog_and_saved_templates(self):
        PrintSettings.objects.create(
            name='Шаблон работы',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[{'type': 'header'}],
        )

        response = self.client.get(
            reverse('document_engine:print-profile-editor'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_engine/print_settings_editor.html',
        )
        self.assertContains(response, 'Настройки печати')
        self.assertContains(response, 'Контрольная / самостоятельная')
        self.assertContains(response, 'Шаблон работы')
        self.assertContains(response, 'header')
        self.assertContains(response, 'HTML')
        self.assertContains(response, 'PDF')
        self.assertContains(response, 'LaTeX')
        self.assertContains(
            response,
            reverse('document_engine:print-profile-create'),
        )
        self.assertContains(
            response,
            reverse(
                'document_engine:print-profile-update',
                args=[PrintSettings.objects.get(name='Шаблон работы').pk],
            ),
        )

    def test_print_settings_editor_passes_query_filters_to_clean_use_case(self):
        response = self.client.get(
            reverse('document_engine:print-profile-editor'),
            {'type': 'work', 'renderable': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_document_type'], 'work')
        self.assertTrue(response.context['renderable_only'])
        self.assertContains(response, 'value="work" selected')
        self.assertContains(
            response,
            'href="?type=remedial_sheet&amp;renderable=1"',
        )

    def test_print_settings_create_view_shows_section_form(self):
        response = self.client.get(
            reverse('document_engine:print-profile-create'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_engine/print_settings_form.html',
        )
        self.assertContains(response, 'Новые настройки печати')
        self.assertContains(response, 'name="document_type"')
        self.assertContains(response, 'value="header"')
        self.assertContains(response, 'value="task_list"')
        self.assertContains(response, 'name="section_options__task_list"')
        self.assertContains(response, 'role_render_modes')
        self.assertContains(response, 'data-section-options-example')
        self.assertContains(response, 'name="section_options__blank_cells"')
        self.assertNotContains(response, 'name="section_options__header"')
        self.assertContains(response, 'Порядок секций')
        self.assertContains(response, 'можно повторять')
        self.assertContains(response, 'Повторяемые:')
        self.assertContains(response, 'common_header,header,task_list,page_break')
        self.assertContains(response, 'header,theory,full_solutions,task_list')
        self.assertContains(response, 'Оформление документа')
        self.assertContains(response, 'name="custom_css"')
        self.assertContains(response, 'name="custom_latex_preamble"')
        self.assertContains(response, 'name="html_template_override"')
        self.assertContains(response, 'name="latex_template_override"')

    def test_print_settings_create_view_creates_template(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Шаблон работы',
                'description': 'Для печати',
                'document_type': 'work',
                'sections': ['header', 'task_list'],
                'is_default': 'on',
                'custom_css': 'body { font-size: 12pt; }',
                'custom_latex_preamble': '\\usepackage{multicol}',
                'html_template_override': '<main>{{ body_content }}</main>',
                'latex_template_override': (
                    '\\begin{document}{{ body_content }}'
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template = PrintSettings.objects.get(name='Шаблон работы')
        self.assertEqual(template.description, 'Для печати')
        self.assertEqual(
            template.sections_config,
            [{'type': 'header'}, {'type': 'task_list'}],
        )
        self.assertTrue(template.is_default)
        self.assertEqual(template.custom_css, 'body { font-size: 12pt; }')
        self.assertEqual(
            template.custom_latex_preamble,
            '\\usepackage{multicol}',
        )
        self.assertEqual(
            template.html_template_override,
            '<main>{{ body_content }}</main>',
        )
        self.assertEqual(
            template.latex_template_override,
            '\\begin{document}{{ body_content }}',
        )

    def test_print_settings_create_view_preserves_section_order(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Рабочий лист',
                'document_type': 'work',
                'sections': ['header', 'task_list'],
                'section_order': 'task_list,header',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template = PrintSettings.objects.get(name='Рабочий лист')
        self.assertEqual(
            template.sections_config,
            [{'type': 'task_list'}, {'type': 'header'}],
        )

    def test_print_settings_create_view_saves_section_options(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Рабочий лист',
                'document_type': 'work',
                'sections': ['header', 'task_list'],
                'section_options__task_list': (
                    '{"hidden_roles": ["demo"], '
                    '"role_blank_cells": {"practice": {"rows": 6}}}'
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template = PrintSettings.objects.get(name='Рабочий лист')
        self.assertEqual(
            template.sections_config,
            [
                {'type': 'header'},
                {
                    'type': 'task_list',
                    'params': {
                        'hidden_roles': ['demo'],
                        'role_blank_cells': {'practice': {'rows': 6}},
                    },
                },
            ],
        )

    def test_print_settings_create_view_shows_invalid_section_options_error(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Рабочий лист',
                'document_type': 'work',
                'sections': ['task_list'],
                'section_options__task_list': '{"hidden_roles":',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Настройки секции task_list: некорректный JSON.',
        )
        self.assertFalse(PrintSettings.objects.exists())

    def test_print_settings_create_view_shows_clean_validation_errors(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Шаблон РнО',
                'document_type': 'remedial_sheet',
                'sections': ['task_list'],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Section task_list is not supported for document type remedial_sheet',
        )
        self.assertFalse(PrintSettings.objects.exists())

    def test_print_settings_update_view_shows_existing_template(self):
        template = PrintSettings.objects.create(
            name='Шаблон работы',
            description='Описание',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[{'type': 'header'}],
            is_default=True,
            custom_css='body { color: black; }',
            custom_latex_preamble='\\usepackage{geometry}',
            html_template_override='<main>{{ body_content }}</main>',
            latex_template_override='\\begin{document}{{ body_content }}',
        )

        response = self.client.get(
            reverse('document_engine:print-profile-update', args=[template.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_engine/print_settings_form.html',
        )
        self.assertContains(response, 'Редактирование настроек печати')
        self.assertContains(response, 'value="Шаблон работы"')
        self.assertContains(response, 'Описание')
        self.assertContains(response, 'value="header"')
        self.assertContains(response, 'body { color: black; }')
        self.assertContains(response, '\\usepackage{geometry}')
        self.assertContains(
            response,
            '&lt;main&gt;{{ body_content }}&lt;/main&gt;',
        )
        self.assertContains(
            response,
            '\\begin{document}{{ body_content }}',
        )
        self.assertContains(response, 'checked')

    def test_print_settings_update_view_shows_existing_section_options(self):
        template = PrintSettings.objects.create(
            name='Шаблон работы',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[
                {'type': 'header'},
                {
                    'type': 'task_list',
                    'params': {
                        'hidden_roles': ['demo'],
                        'role_blank_cells': {'practice': {'rows': 6}},
                    },
                },
            ],
        )

        response = self.client.get(
            reverse('document_engine:print-profile-update', args=[template.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '&quot;hidden_roles&quot;: [')
        self.assertContains(response, '&quot;role_blank_cells&quot;: {')
        self.assertContains(response, '&quot;rows&quot;: 6')

    def test_print_settings_update_view_updates_template(self):
        template = PrintSettings.objects.create(
            name='Старый шаблон',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[{'type': 'header'}],
        )

        response = self.client.post(
            reverse('document_engine:print-profile-update', args=[template.pk]),
            {
                'name': 'Новый шаблон',
                'description': 'Новое описание',
                'document_type': 'work',
                'sections': ['header', 'task_list'],
                'is_default': 'on',
                'custom_css': '.task { margin: 1rem; }',
                'custom_latex_preamble': '\\usepackage{multicol}',
                'html_template_override': '<article>{{ body_content }}</article>',
                'latex_template_override': '\\section*{Лист}{{ body_content }}',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template.refresh_from_db()
        self.assertEqual(template.name, 'Новый шаблон')
        self.assertEqual(template.description, 'Новое описание')
        self.assertEqual(
            template.sections_config,
            [{'type': 'header'}, {'type': 'task_list'}],
        )
        self.assertTrue(template.is_default)
        self.assertEqual(template.custom_css, '.task { margin: 1rem; }')
        self.assertEqual(
            template.custom_latex_preamble,
            '\\usepackage{multicol}',
        )
        self.assertEqual(
            template.html_template_override,
            '<article>{{ body_content }}</article>',
        )
        self.assertEqual(
            template.latex_template_override,
            '\\section*{Лист}{{ body_content }}',
        )

    def test_print_settings_update_view_preserves_section_order(self):
        template = PrintSettings.objects.create(
            name='Старый шаблон',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[{'type': 'header'}],
        )

        response = self.client.post(
            reverse('document_engine:print-profile-update', args=[template.pk]),
            {
                'name': 'Новый шаблон',
                'document_type': 'work',
                'sections': ['header', 'task_list'],
                'section_order': 'task_list,header',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template.refresh_from_db()
        self.assertEqual(
            template.sections_config,
            [{'type': 'task_list'}, {'type': 'header'}],
        )

    def test_print_settings_update_view_returns_404_for_missing_template(self):
        response = self.client.get(
            reverse(
                'document_engine:print-profile-update',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            ),
        )

        self.assertEqual(response.status_code, 404)
