from django.test import SimpleTestCase

from core_logic.entities.document import Document, DocumentSection
from infrastructure.services.document_content_config import (
    content_config_from_document,
)


class DocumentContentConfigTests(SimpleTestCase):
    def test_maps_plain_task_document_to_legacy_config(self):
        document = Document(
            title='Контрольная',
            document_type='work',
            sections=[
                DocumentSection(
                    section_type='task_variants',
                    payload={
                        'include_hints': True,
                        'include_instructions': False,
                    },
                ),
            ],
        )

        self.assertEqual(
            content_config_from_document(document),
            {
                'include_answers': False,
                'include_short_solutions': False,
                'include_full_solutions': False,
                'answer_type': 'tasks_only',
                'include_hints': True,
                'include_instructions': False,
            },
        )

    def test_maps_full_solution_document_to_legacy_config(self):
        document = Document(
            title='Контрольная',
            document_type='work',
            sections=[
                DocumentSection(section_type='task_variants'),
                DocumentSection(section_type='answers'),
                DocumentSection(section_type='short_solutions'),
                DocumentSection(section_type='full_solutions'),
            ],
        )

        self.assertEqual(
            content_config_from_document(document),
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': True,
                'answer_type': 'with_full_solutions',
                'include_hints': False,
                'include_instructions': False,
            },
        )

    def test_maps_short_solutions_to_include_answers(self):
        document = Document(
            title='Разбор',
            document_type='remedial_sheet',
            sections=[
                DocumentSection(section_type='original_mistakes'),
                DocumentSection(section_type='training_tasks'),
                DocumentSection(section_type='short_solutions'),
            ],
        )

        self.assertEqual(
            content_config_from_document(document),
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': False,
                'answer_type': 'with_short_solutions',
                'include_hints': False,
                'include_instructions': False,
            },
        )
