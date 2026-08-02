from django.test import TestCase
from django.urls import reverse

from document_engine.models import PrintSettings
from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
)


class PresentationProfileViewTests(TestCase):
    def test_editor_shows_presentation_profiles_without_section_controls(self):
        profile = PrintSettings.objects.create(
            name='Оформление работы',
            document_type=PrintSettings.DocumentType.WORK,
            custom_css='body { font-size: 14px; }',
            custom_latex_preamble='\\small',
        )

        response = self.client.get(
            reverse('document_engine:print-profile-editor'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'document_engine/presentation_profile_editor.html',
        )
        self.assertContains(response, 'Профили оформления')
        self.assertContains(response, 'Оформление работы')
        self.assertContains(response, 'Спецификация работы')
        self.assertContains(response, 'Снимок варианта')
        self.assertContains(response, 'CSS')
        self.assertContains(response, 'LaTeX')
        self.assertNotContains(response, 'Порядок секций')
        self.assertContains(
            response,
            reverse(
                'document_engine:print-profile-update',
                args=[profile.pk],
            ),
        )

    def test_editor_passes_query_filters_to_clean_use_case(self):
        response = self.client.get(
            reverse('document_engine:print-profile-editor'),
            {'type': 'work', 'renderable': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_document_type'], 'work')
        self.assertTrue(response.context['renderable_only'])
        self.assertContains(response, 'value="work" selected')

    def test_create_view_shows_only_presentation_controls(self):
        response = self.client.get(
            reverse('document_engine:print-profile-create'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новый профиль оформления')
        self.assertContains(response, 'не меняет спецификацию работы')
        self.assertContains(response, 'name="custom_css"')
        self.assertContains(response, 'name="custom_latex_preamble"')
        self.assertContains(response, 'name="html_template_override"')
        self.assertContains(response, 'name="latex_template_override"')
        self.assertContains(response, 'data-style-example="css"')
        self.assertContains(response, 'schooltasklist')
        self.assertNotContains(response, 'name="sections"')
        self.assertNotContains(response, 'name="section_order"')

    def test_create_view_creates_presentation_profile(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Оформление работы',
                'description': 'Для печати',
                'document_type': 'work',
                'is_default': 'on',
                'custom_css': 'body { font-size: 12pt; }',
                'custom_latex_preamble': '\\usepackage{multicol}',
                'html_template_override': (
                    '<main>{{ body_content|safe }}</main>'
                ),
                'latex_template_override': (
                    '\\begin{document}{{ body_content|safe }}\\end{document}'
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        profile = PrintSettings.objects.get(name='Оформление работы')
        self.assertEqual(profile.description, 'Для печати')
        self.assertTrue(profile.is_default)
        self.assertEqual(profile.custom_css, 'body { font-size: 12pt; }')
        self.assertEqual(
            profile.custom_latex_preamble,
            '\\usepackage{multicol}',
        )

    def test_create_view_rejects_wrapper_without_document_body(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Сломанная обёртка',
                'document_type': 'work',
                'html_template_override': '<html></html>',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'HTML-обёртка должна содержать',
        )
        self.assertFalse(
            PrintSettings.objects.filter(name='Сломанная обёртка').exists(),
        )

    def test_create_view_discards_latex_for_html_only_report(self):
        response = self.client.post(
            reverse('document_engine:print-profile-create'),
            {
                'name': 'Оформление отчёта',
                'document_type': EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
                'custom_css': '.report-metric { padding: 2mm; }',
                'custom_latex_preamble': '\\small',
                'latex_template_override': 'not a valid wrapper',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        profile = PrintSettings.objects.get(name='Оформление отчёта')
        self.assertEqual(profile.custom_latex_preamble, '')
        self.assertEqual(profile.latex_template_override, '')

    def test_update_view_shows_existing_presentation(self):
        profile = PrintSettings.objects.create(
            name='Оформление работы',
            description='Описание',
            document_type=PrintSettings.DocumentType.WORK,
            custom_css='body { color: black; }',
            is_default=True,
        )

        response = self.client.get(
            reverse(
                'document_engine:print-profile-update',
                args=[profile.pk],
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Редактирование профиля оформления')
        self.assertContains(response, 'Оформление работы')
        self.assertContains(response, 'body { color: black; }')
        self.assertContains(response, 'name="is_default"')

    def test_update_view_updates_presentation(self):
        profile = PrintSettings.objects.create(
            name='Старый профиль',
            document_type=PrintSettings.DocumentType.WORK,
        )

        response = self.client.post(
            reverse(
                'document_engine:print-profile-update',
                args=[profile.pk],
            ),
            {
                'name': 'Новый профиль',
                'description': 'Новое описание',
                'document_type': 'work',
                'custom_css': '.task-item { margin: 1rem; }',
            },
        )

        self.assertRedirects(
            response,
            reverse('document_engine:print-profile-editor'),
        )
        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Новый профиль')
        self.assertEqual(profile.description, 'Новое описание')
        self.assertEqual(
            profile.custom_css,
            '.task-item { margin: 1rem; }',
        )

    def test_update_view_returns_404_for_missing_profile(self):
        response = self.client.get(
            reverse(
                'document_engine:print-profile-update',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            ),
        )

        self.assertEqual(response.status_code, 404)
