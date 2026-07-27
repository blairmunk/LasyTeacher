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
        self.assertNotContains(response, 'name="section_options__task_list"')
        self.assertContains(response, 'name="task_list_structured_options"')
        self.assertContains(response, 'name="task_list_demo_visible"')
        self.assertContains(
            response,
            'name="task_list_theory_visible"',
        )
        self.assertContains(
            response,
            'name="task_list_text_visible"',
        )
        self.assertContains(
            response,
            'name="task_list_content_visibility_options"',
        )
        self.assertContains(response, 'name="task_list_demo_render_mode"')
        self.assertContains(
            response,
            'name="task_list_practice_blank_cells_mode"',
        )
        self.assertContains(
            response,
            'name="task_list_practice_blank_cells_rows"',
        )
        self.assertNotContains(response, 'name="section_options__blank_cells"')
        self.assertContains(response, 'name="blank_cells_rows"')
        self.assertContains(response, 'name="blank_cells_columns"')
        self.assertContains(response, 'name="blank_cells_row_height"')
        self.assertNotContains(response, 'name="section_options__theory"')
        self.assertContains(response, 'name="theory_structured_options"')
        self.assertContains(response, 'name="theory_section_title"')
        self.assertContains(response, 'name="theory_include_subtopics"')
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

    def test_print_settings_create_view_saves_blank_cells_controls(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Лист с полем решения',
                'document_type': 'work',
                'sections': ['header', 'blank_cells'],
                'blank_cells_rows': '9',
                'blank_cells_columns': '18',
                'blank_cells_row_height': '28',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template = PrintSettings.objects.get(name='Лист с полем решения')
        self.assertEqual(
            template.sections_config,
            [
                {'type': 'header'},
                {
                    'type': 'blank_cells',
                    'params': {
                        'rows': 9,
                        'columns': 18,
                        'row_height': 28,
                    },
                },
            ],
        )

    def test_print_settings_create_view_saves_task_list_role_controls(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Ролевой рабочий лист',
                'document_type': 'work',
                'sections': ['header', 'task_list'],
                'task_list_structured_options': '1',
                'task_list_demo_visible': 'on',
                'task_list_demo_render_mode': 'with_full_solution',
                'task_list_demo_blank_cells_mode': 'hide',
                'task_list_practice_visible': 'on',
                'task_list_practice_render_mode': 'task_only',
                'task_list_practice_blank_cells_mode': 'show',
                'task_list_practice_blank_cells_rows': '8',
                'task_list_control_visible': 'on',
                'task_list_control_blank_cells_mode': '',
                'task_list_remedial_blank_cells_mode': '',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template = PrintSettings.objects.get(name='Ролевой рабочий лист')
        self.assertEqual(
            template.sections_config,
            [
                {'type': 'header'},
                {
                    'type': 'task_list',
                    'params': {
                        'hidden_roles': ['remedial'],
                        'role_render_modes': {
                            'demo': 'with_full_solution',
                            'practice': 'task_only',
                        },
                        'role_blank_cells': {
                            'demo': False,
                            'practice': {'rows': 8},
                        },
                    },
                },
            ],
        )

    def test_print_settings_create_view_saves_theory_controls(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Лист с теорией',
                'document_type': 'work',
                'sections': ['header', 'theory', 'task_list'],
                'theory_structured_options': '1',
                'theory_section_title': 'Перед началом работы',
                'theory_include_subtopics': 'on',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template = PrintSettings.objects.get(name='Лист с теорией')
        self.assertEqual(
            template.sections_config,
            [
                {'type': 'header'},
                {
                    'type': 'theory',
                    'params': {
                        'section_title': 'Перед началом работы',
                        'include_subtopics': True,
                    },
                },
                {'type': 'task_list'},
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
        form = response.context['form']
        self.assertFalse(form['task_list_demo_visible'].value())
        self.assertEqual(
            form['task_list_practice_blank_cells_mode'].value(),
            'show',
        )
        self.assertEqual(
            form['task_list_practice_blank_cells_rows'].value(),
            6,
        )

    def test_print_settings_update_view_shows_existing_theory_options(self):
        template = PrintSettings.objects.create(
            name='Теоретический лист',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[
                {
                    'type': 'theory',
                    'params': {
                        'section_title': 'Опорный конспект',
                        'include_subtopics': True,
                    },
                },
                {'type': 'task_list'},
            ],
        )

        response = self.client.get(
            reverse('document_engine:print-profile-update', args=[template.pk]),
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(
            form['theory_section_title'].value(),
            'Опорный конспект',
        )
        self.assertTrue(form['theory_include_subtopics'].value())

    def test_update_preserves_distinct_repeated_section_settings(self):
        template = PrintSettings.objects.create(
            name='Лист с двумя полями',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[
                {
                    'type': 'blank_cells',
                    'title': 'Короткое решение',
                    'params': {
                        'rows': 4,
                        'columns': 12,
                        'row_height': 20,
                    },
                },
                {
                    'type': 'blank_cells',
                    'title': 'Большое решение',
                    'params': {
                        'rows': 10,
                        'columns': 24,
                        'row_height': 30,
                    },
                },
            ],
        )
        update_url = reverse(
            'document_engine:print-profile-update',
            args=[template.pk],
        )

        get_response = self.client.get(update_url)

        self.assertEqual(get_response.status_code, 200)
        self.assertContains(
            get_response,
            'Повторы этой секции имеют разные настройки.',
        )

        response = self.client.post(
            update_url,
            {
                'name': 'Лист с двумя полями',
                'document_type': 'work',
                'sections': ['blank_cells'],
                'section_order': 'blank_cells,blank_cells',
                'blank_cells_rows': '4',
                'blank_cells_columns': '12',
                'blank_cells_row_height': '20',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        template.refresh_from_db()
        self.assertEqual(
            template.sections_config,
            [
                {
                    'type': 'blank_cells',
                    'title': 'Короткое решение',
                    'params': {
                        'rows': 4,
                        'columns': 12,
                        'row_height': 20,
                    },
                },
                {
                    'type': 'blank_cells',
                    'title': 'Большое решение',
                    'params': {
                        'rows': 10,
                        'columns': 24,
                        'row_height': 30,
                    },
                },
            ],
        )

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
