import datetime as dt
from unittest import TestCase

from core_logic.entities.document import DocumentPresentation
from core_logic.entities.student_digest import (
    StudentDigestOptions,
    StudentDigestRequest,
)
from core_logic.value_objects.document_recipe_factories import (
    build_event_performance_report_document_recipe,
    build_student_digest_document_recipe,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_student_digest_document_recipe_for_render,
)
from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    EVENT_REPORT_CONCLUSIONS_SECTION,
    EVENT_REPORT_SUMMARY_SECTION,
    EVENT_REPORT_SPECIFICATION_SECTION,
    EVENT_REPORT_TASK_ANALYSIS_SECTION,
    EVENT_REPORT_TEACHER_NOTES_SECTION,
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    STUDENT_DIGEST_DETAILS_SECTION,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    STUDENT_DIGEST_FOCUS_SECTION,
    STUDENT_DIGEST_SUMMARY_SECTION,
    STUDENT_DIGEST_TEACHER_COMMENTS_SECTION,
)


class ReportDocumentRecipeTests(TestCase):
    def test_builds_event_report_recipe_in_semantic_order(self):
        recipe = build_event_performance_report_document_recipe()

        self.assertEqual(
            recipe.document_type,
            EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
        )
        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                EVENT_REPORT_SPECIFICATION_SECTION,
                EVENT_REPORT_SUMMARY_SECTION,
                EVENT_REPORT_TASK_ANALYSIS_SECTION,
                EVENT_REPORT_CONCLUSIONS_SECTION,
            ),
        )

    def test_builds_event_report_with_explicit_optional_materials(self):
        recipe = build_event_performance_report_document_recipe(
            include_content_element_text=False,
            include_teacher_notes=True,
        )

        self.assertFalse(
            recipe.sections[1].options['include_content_element_text'],
        )
        self.assertEqual(
            recipe.section_types[-1],
            EVENT_REPORT_TEACHER_NOTES_SECTION,
        )

    def test_builds_digest_recipe_from_content_options(self):
        recipe = build_student_digest_document_recipe(
            StudentDigestOptions(
                include_summary=True,
                include_details=True,
                include_focus=True,
                include_retakes=False,
            ),
        )

        self.assertEqual(recipe.document_type, STUDENT_DIGEST_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                STUDENT_DIGEST_SUMMARY_SECTION,
                STUDENT_DIGEST_DETAILS_SECTION,
                STUDENT_DIGEST_FOCUS_SECTION,
            ),
        )

    def test_expands_complete_digest_recipe_per_student(self):
        request = StudentDigestRequest(
            group_id='group-1',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2026, 9, 7),
            options=StudentDigestOptions(
                include_summary=True,
                include_details=True,
                include_focus=False,
                include_retakes=False,
            ),
        )

        recipe = build_student_digest_document_recipe_for_render(
            digest_request=request,
            student_ids=['student-1', 'student-2'],
        )

        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                STUDENT_DIGEST_SUMMARY_SECTION,
                STUDENT_DIGEST_DETAILS_SECTION,
                PAGE_BREAK_SECTION,
                HEADER_SECTION,
                STUDENT_DIGEST_SUMMARY_SECTION,
                STUDENT_DIGEST_DETAILS_SECTION,
            ),
        )
        self.assertEqual(
            recipe.sections[0].options['student_id'],
            'student-1',
        )
        self.assertIs(recipe.sections[0].options['digest_request'], request)
        self.assertEqual(
            recipe.sections[-1].options['student_id'],
            'student-2',
        )

    def test_builds_teacher_comments_independently_from_digest_details(self):
        recipe = build_student_digest_document_recipe(
            StudentDigestOptions(
                include_summary=False,
                include_details=False,
                include_focus=False,
                include_retakes=False,
                include_teacher_comments=True,
            ),
        )

        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, STUDENT_DIGEST_TEACHER_COMMENTS_SECTION),
        )

    def test_preserves_presentation_when_expanding_digest(self):
        request = StudentDigestRequest(
            options=StudentDigestOptions(include_details=False),
        )
        presentation = DocumentPresentation(custom_css='.digest { color:red; }')

        from core_logic.entities.document import DocumentPresentationProfile

        recipe = build_student_digest_document_recipe_for_render(
            digest_request=request,
            student_ids=['student-1'],
            presentation_profile=DocumentPresentationProfile(
                name='Compact',
                document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
                presentation=presentation,
            ),
        )

        self.assertEqual(recipe.presentation, presentation)
