from unittest import TestCase

from core_logic.value_objects.content_config import (
    RemedialSheetGenerationOptions,
    WorkGenerationOptions,
    build_remedial_sheet_generation_options,
    build_work_generation_options,
)


class WorkGenerationOptionsTests(TestCase):
    def test_builds_default_work_generation_options(self):
        options = build_work_generation_options({})

        self.assertEqual(options.generator_type, 'pdf')
        self.assertEqual(options.renderer_type, 'pdf')
        self.assertEqual(options.pdf_format, 'A4')
        self.assertEqual(options.answer_type, 'tasks_only')
        self.assertEqual(options.content_description, 'только задания')
        self.assertEqual(
            options.content_config,
            {
                'include_answers': False,
                'include_short_solutions': False,
                'include_full_solutions': False,
                'answer_type': 'tasks_only',
                'include_hints': False,
                'include_instructions': False,
            },
        )

    def test_supports_legacy_with_answers_flag(self):
        options = build_work_generation_options({
            'answer_type': 'tasks_only',
            'with_answers': '1',
        })

        self.assertEqual(options.answer_type, 'with_answers')
        self.assertEqual(options.content_description, 'с ответами')
        self.assertTrue(options.content_config['include_answers'])

    def test_builds_full_solution_work_generation_options(self):
        options = build_work_generation_options({
            'generator_type': 'html',
            'format': 'A5',
            'answer_type': 'with_full_solutions',
            'include_hints': '1',
            'include_instructions': '1',
        })

        self.assertEqual(options.generator_type, 'html')
        self.assertEqual(options.renderer_type, 'html')
        self.assertEqual(options.file_type_label, 'HTML')
        self.assertEqual(options.pdf_format, 'A5')
        self.assertEqual(
            options.content_description,
            'с полными решениями + подсказки + инструкции',
        )
        self.assertEqual(
            options.content_config,
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': True,
                'answer_type': 'with_full_solutions',
                'include_hints': True,
                'include_instructions': True,
            },
        )

    def test_builds_default_remedial_sheet_generation_options(self):
        options = build_remedial_sheet_generation_options({})

        self.assertEqual(options.generator_type, 'pdf')
        self.assertEqual(options.renderer_type, 'pdf')
        self.assertEqual(options.pdf_format, 'A4')
        self.assertEqual(options.answer_type, 'with_short_solutions')
        self.assertEqual(
            options.content_config,
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': False,
                'page_format': 'A4',
            },
        )

    def test_builds_work_options_from_renderer_type(self):
        options = build_work_generation_options({
            'renderer_type': 'html',
            'generator_type': 'pdf',
        })

        self.assertEqual(options.renderer_type, 'html')

    def test_builds_remedial_sheet_options_from_renderer_type(self):
        options = build_remedial_sheet_generation_options({
            'renderer_type': 'html',
            'generator_type': 'pdf',
        })

        self.assertEqual(options.renderer_type, 'html')

    def test_work_options_keep_legacy_generator_type_keyword(self):
        options = WorkGenerationOptions(generator_type='html')

        self.assertEqual(options.renderer_type, 'html')
        self.assertEqual(options.generator_type, 'html')

    def test_remedial_sheet_options_keep_legacy_generator_type_keyword(self):
        options = RemedialSheetGenerationOptions(generator_type='html')

        self.assertEqual(options.renderer_type, 'html')
        self.assertEqual(options.generator_type, 'html')
