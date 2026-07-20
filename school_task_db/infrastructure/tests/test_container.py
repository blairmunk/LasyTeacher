from unittest.mock import patch

from django.test import SimpleTestCase

from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
from core_logic.use_cases.assign_event_variants import AssignEventVariantsUseCase
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsUseCase
from core_logic.use_cases.bulk_change_task_groups import (
    BulkAddTasksToGroupUseCase,
    BulkCreateGroupFromTasksUseCase,
    BulkRemoveTasksFromGroupsUseCase,
)
from core_logic.use_cases.calculate_review_score import CalculateReviewScoreUseCase
from core_logic.use_cases.change_event_status import ChangeEventStatusUseCase
from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupUseCase,
    RemoveTaskFromGroupUseCase,
)
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.create_source import CreateSourceUseCase
from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkUseCase,
)
from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantUseCase,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansUseCase,
)
from core_logic.use_cases.create_work_from_groups import (
    CreateWorkFromGroupsUseCase,
)
from core_logic.use_cases.create_work_from_tasks import CreateWorkFromTasksUseCase
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsUseCase
from core_logic.use_cases.delete_task import DeleteTaskUseCase
from core_logic.use_cases.delete_variant import DeleteVariantUseCase
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.use_cases.export_tasks import ExportTasksUseCase
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
from core_logic.use_cases.compose_work_variants import ComposeWorkVariantsUseCase
from core_logic.use_cases.generate_work_variants import GenerateWorkVariantsUseCase
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.get_add_tasks_to_group import GetAddTasksToGroupUseCase
from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase
from core_logic.use_cases.get_course_list import GetCourseListUseCase
from core_logic.use_cases.get_topic_detail import GetTopicDetailUseCase
from core_logic.use_cases.get_topic_list import GetTopicListUseCase
from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase
from core_logic.use_cases.get_default_document_template import (
    GetDefaultDocumentTemplateUseCase,
)
from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListUseCase,
)
from core_logic.use_cases.get_global_search import GetGlobalSearchUseCase
from core_logic.use_cases.get_heatmap_course_overview import (
    GetHeatmapCourseOverviewUseCase,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    GetHeatmapCourseTopicMatrixUseCase,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    GetHeatmapCourseTimelineUseCase,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    GetHeatmapDrilldownOverviewUseCase,
)
from core_logic.use_cases.get_heatmap_overview import GetHeatmapOverviewUseCase
from core_logic.use_cases.get_heatmap_student_detail import (
    GetHeatmapStudentDetailUseCase,
)
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    GetHeatmapSubtopicDetailUseCase,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    GetHeatmapSubtopicMatrixUseCase,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    GetHeatmapTopicMatrixUseCase,
)
from core_logic.use_cases.get_import_views import (
    GetImportHistoryUseCase,
    GetImportPageUseCase,
)
from core_logic.use_cases.get_journal import GetJournalUseCase
from core_logic.use_cases.get_journal_select import GetJournalSelectUseCase
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)
from core_logic.use_cases.get_event_review import GetEventReviewUseCase
from core_logic.use_cases.get_event_detail import GetEventDetailUseCase
from core_logic.use_cases.get_event_list import GetEventListUseCase
from core_logic.use_cases.get_event_participant_selection import (
    GetEventParticipantSelectionUseCase,
)
from core_logic.use_cases.get_event_participation_ref import (
    GetEventParticipationRefUseCase,
)
from core_logic.use_cases.get_event_variant_assignment import (
    GetEventVariantAssignmentUseCase,
)
from core_logic.use_cases.get_events_status_report import (
    GetEventsStatusReportUseCase,
)
from core_logic.use_cases.get_generated_document_file import (
    GetGeneratedDocumentFileUseCase,
)
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileUseCase,
)
from core_logic.use_cases.get_orphan_variant_list import GetOrphanVariantListUseCase
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_remedial_wizard_preview import (
    GetRemedialWizardPreviewUseCase,
)
from core_logic.use_cases.get_remedial_wizard_start import (
    GetRemedialWizardStartUseCase,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentUseCase
from core_logic.use_cases.get_recent_review_sessions import (
    GetRecentReviewSessionsUseCase,
)
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.get_site_settings import GetSiteSettingsUseCase
from core_logic.use_cases.get_student_detail import GetStudentDetailUseCase
from core_logic.use_cases.get_student_group_detail import GetStudentGroupDetailUseCase
from core_logic.use_cases.get_student_group_list import GetStudentGroupListUseCase
from core_logic.use_cases.get_student_list import GetStudentListUseCase
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_db_health import GetTaskDBHealthUseCase
from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase
from core_logic.use_cases.get_task_group_list import GetTaskGroupListUseCase
from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase
from core_logic.use_cases.get_task_list import GetTaskListUseCase
from core_logic.use_cases.get_task_reference_options import (
    GetCodifierElementsUseCase,
    GetSubtopicOptionsUseCase,
)
from core_logic.use_cases.get_topic_subtopics import GetTopicSubtopicsUseCase
from core_logic.use_cases.get_source_list import GetSourceListUseCase
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.get_variant_detail import GetVariantDetailUseCase
from core_logic.use_cases.get_variant_generation_placeholder import (
    GetVariantGenerationPlaceholderUseCase,
)
from core_logic.use_cases.get_variant_generation_form import (
    GetVariantGenerationFormUseCase,
)
from core_logic.use_cases.get_variant_list import GetVariantListUseCase
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.get_work_form_data import GetWorkFormDataUseCase
from core_logic.use_cases.get_work_list import GetWorkListUseCase
from core_logic.use_cases.get_work_analysis_report import (
    GetWorkAnalysisReportUseCase,
)
from core_logic.use_cases.get_reports_dashboard import GetReportsDashboardUseCase
from core_logic.use_cases.get_student_performance_report import (
    GetStudentPerformanceReportUseCase,
)
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionUseCase,
)
from core_logic.use_cases.preview_task_import import PreviewTaskImportUseCase
from core_logic.use_cases.refresh_task_math_cache import RefreshTaskMathCacheUseCase
from core_logic.use_cases.save_analog_group import (
    CreateAnalogGroupUseCase,
    UpdateAnalogGroupUseCase,
)
from core_logic.use_cases.save_event import CreateEventUseCase, UpdateEventUseCase
from core_logic.use_cases.save_student import (
    CreateStudentGroupUseCase,
    CreateStudentUseCase,
    UpdateStudentGroupUseCase,
    UpdateStudentUseCase,
)
from core_logic.use_cases.save_site_settings import SaveSiteSettingsUseCase
from core_logic.use_cases.save_task import (
    CreateTaskUseCase,
    SaveTaskImagesUseCase,
    UpdateTaskUseCase,
)
from core_logic.use_cases.save_work import (
    CreateWorkUseCase,
    SaveWorkSpecificationUseCase,
    UpdateWorkUseCase,
)
from core_logic.use_cases.sync_review_session import SyncReviewSessionUseCase
from core_logic.use_cases.sync_work_analog_groups import SyncWorkAnalogGroupsUseCase
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentUseCase,
)
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonUseCase,
)
from core_logic.use_cases.validate_review_work_scan import ValidateReviewWorkScanUseCase
from infrastructure.repositories.django_codifier_repo import DjangoCodifierRepository
from infrastructure.repositories.django_core_repo import DjangoCoreRepository
from infrastructure.repositories.django_curriculum_repo import (
    DjangoCurriculumRepository,
)
from infrastructure.repositories.django_document_template_repo import (
    DjangoDocumentTemplateRepository,
)
from infrastructure.container import Container
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_report_repo import DjangoReportRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_settings_repo import DjangoSettingsRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.report_forms import ReportFormAdapter
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.work_forms import WorkFormAdapter
from infrastructure.services.document_engine import (
    DjangoDocumentEngine,
)
from infrastructure.services.task_import_service import DjangoTaskImportService


class ContainerTests(SimpleTestCase):
    def test_document_engine_uses_sectioned_renderer_factory(self):
        container = Container()
        remedial_sheet_data_use_case = object()
        engine = object()

        with patch.object(
            container,
            'get_remedial_sheet_data_use_case',
            return_value=remedial_sheet_data_use_case,
        ), patch.object(
            DjangoDocumentEngine,
            'with_sectioned_renderers',
            return_value=engine,
        ) as factory:
            result = container.document_engine

        self.assertIs(result, engine)
        factory.assert_called_once_with(
            get_remedial_sheet_data_use_case=remedial_sheet_data_use_case,
        )

    def test_wires_remedial_from_event_use_case(self):
        container = Container()

        use_case = container.create_remedial_from_event_use_case()
        wizard_create_use_case = container.create_remedial_wizard_work_use_case()
        preview_use_case = container.get_remedial_event_preview_use_case()
        create_event_use_case = container.create_event_use_case()
        update_event_use_case = container.update_event_use_case()
        wizard_preview_use_case = container.get_remedial_wizard_preview_use_case()
        wizard_start_use_case = container.get_remedial_wizard_start_use_case()
        profile_use_case = container.get_student_profile_use_case()
        task_list_use_case = container.get_task_list_use_case()
        task_detail_use_case = container.get_task_detail_use_case()
        subtopic_options_use_case = container.get_subtopic_options_use_case()
        codifier_elements_use_case = container.get_codifier_elements_use_case()
        source_list_use_case = container.get_source_list_use_case()
        document_template_list_use_case = (
            container.get_document_template_list_use_case()
        )
        default_document_template_use_case = (
            container.get_default_document_template_use_case()
        )
        refresh_math_cache_use_case = container.refresh_task_math_cache_use_case()
        create_task_use_case = container.create_task_use_case()
        update_task_use_case = container.update_task_use_case()
        save_task_images_use_case = container.save_task_images_use_case()
        student_detail_use_case = container.get_student_detail_use_case()
        student_group_detail_use_case = container.get_student_group_detail_use_case()
        student_list_use_case = container.get_student_list_use_case()
        student_group_list_use_case = container.get_student_group_list_use_case()
        student_remedial_use_case = container.get_student_remedial_work_use_case()
        create_student_use_case = container.create_student_use_case()
        update_student_use_case = container.update_student_use_case()
        create_student_group_use_case = container.create_student_group_use_case()
        update_student_group_use_case = container.update_student_group_use_case()
        create_student_remedial_use_case = (
            container.create_student_remedial_variant_use_case()
        )
        grade_use_case = container.grade_student_work_use_case()
        review_use_case = container.get_participation_review_use_case()
        dashboard_use_case = container.get_review_dashboard_use_case()
        event_review_use_case = container.get_event_review_use_case()
        event_list_use_case = container.get_event_list_use_case()
        event_detail_use_case = container.get_event_detail_use_case()
        task_group_detail_use_case = container.get_task_group_detail_use_case()
        task_group_list_use_case = container.get_task_group_list_use_case()
        create_analog_group_use_case = container.create_analog_group_use_case()
        update_analog_group_use_case = container.update_analog_group_use_case()
        add_tasks_form_use_case = container.get_add_tasks_to_group_use_case()
        course_detail_use_case = container.get_course_detail_use_case()
        course_list_use_case = container.get_course_list_use_case()
        topic_subtopics_use_case = container.get_topic_subtopics_use_case()
        topic_list_use_case = container.get_topic_list_use_case()
        topic_detail_use_case = container.get_topic_detail_use_case()
        codifier_list_use_case = container.get_codifier_list_use_case()
        codifier_detail_use_case = container.get_codifier_detail_use_case()
        dashboard_summary_use_case = container.get_dashboard_summary_use_case()
        global_search_use_case = container.get_global_search_use_case()
        heatmap_course_overview_use_case = (
            container.get_heatmap_course_overview_use_case()
        )
        heatmap_course_topic_matrix_use_case = (
            container.get_heatmap_course_topic_matrix_use_case()
        )
        heatmap_course_timeline_use_case = (
            container.get_heatmap_course_timeline_use_case()
        )
        heatmap_drilldown_overview_use_case = (
            container.get_heatmap_drilldown_overview_use_case()
        )
        heatmap_student_detail_use_case = (
            container.get_heatmap_student_detail_use_case()
        )
        heatmap_subtopic_detail_use_case = (
            container.get_heatmap_subtopic_detail_use_case()
        )
        heatmap_overview_use_case = container.get_heatmap_overview_use_case()
        heatmap_subtopic_matrix_use_case = (
            container.get_heatmap_subtopic_matrix_use_case()
        )
        heatmap_topic_matrix_use_case = (
            container.get_heatmap_topic_matrix_use_case()
        )
        import_page_use_case = container.get_import_page_use_case()
        import_history_use_case = container.get_import_history_use_case()
        site_settings_use_case = container.get_site_settings_use_case()
        save_site_settings_use_case = container.save_site_settings_use_case()
        import_validation_use_case = container.validate_task_import_json_use_case()
        execute_import_use_case = container.execute_task_import_use_case()
        preview_import_use_case = container.preview_task_import_use_case()
        sample_import_use_case = container.get_task_import_sample_use_case()
        export_tasks_use_case = container.export_tasks_use_case()
        create_source_use_case = container.create_source_use_case()
        participant_selection_use_case = (
            container.get_event_participant_selection_use_case()
        )
        participation_ref_use_case = container.get_event_participation_ref_use_case()
        variant_assignment_use_case = (
            container.get_event_variant_assignment_use_case()
        )
        events_status_report_use_case = (
            container.get_events_status_report_use_case()
        )
        reports_dashboard_use_case = container.get_reports_dashboard_use_case()
        work_analysis_report_use_case = (
            container.get_work_analysis_report_use_case()
        )
        student_performance_report_use_case = (
            container.get_student_performance_report_use_case()
        )
        journal_select_use_case = container.get_journal_select_use_case()
        journal_use_case = container.get_journal_use_case()
        task_db_health_use_case = container.get_task_db_health_use_case()
        add_participants_use_case = container.add_event_participants_use_case()
        assign_variants_use_case = container.assign_event_variants_use_case()
        assign_single_variant_use_case = (
            container.assign_single_event_variant_use_case()
        )
        change_status_use_case = container.change_event_status_use_case()
        calculate_score_use_case = container.calculate_review_score_use_case()
        finalize_event_use_case = container.finalize_review_event_use_case()
        toggle_absent_use_case = container.toggle_participation_absent_use_case()
        prepare_submission_use_case = (
            container.prepare_participation_review_submission_use_case()
        )
        validate_scan_use_case = container.validate_review_work_scan_use_case()
        save_navigation_use_case = container.get_review_save_navigation_use_case()
        recent_sessions_use_case = container.get_recent_review_sessions_use_case()
        sync_session_use_case = container.sync_review_session_use_case()
        work_detail_use_case = container.get_work_detail_use_case()
        work_form_data_use_case = container.get_work_form_data_use_case()
        work_list_use_case = container.get_work_list_use_case()
        variant_detail_use_case = container.get_variant_detail_use_case()
        variant_generation_use_case = (
            container.get_variant_generation_placeholder_use_case()
        )
        variant_generation_form_use_case = (
            container.get_variant_generation_form_use_case()
        )
        variant_list_use_case = container.get_variant_list_use_case()
        orphan_variant_list_use_case = container.get_orphan_variant_list_use_case()
        sync_work_groups_use_case = container.sync_work_analog_groups_use_case()
        compose_variants_use_case = container.compose_work_variants_use_case()
        generate_variants_use_case = container.generate_work_variants_use_case()
        create_from_orphans_use_case = container.create_work_from_orphans_use_case()
        create_from_groups_use_case = container.create_work_from_groups_use_case()
        create_from_tasks_use_case = container.create_work_from_tasks_use_case()
        create_work_use_case = container.create_work_use_case()
        update_work_use_case = container.update_work_use_case()
        save_work_specification_use_case = (
            container.save_work_specification_use_case()
        )
        variant_delete_info_use_case = container.get_variant_delete_info_use_case()
        delete_variant_use_case = container.delete_variant_use_case()
        delete_task_groups_use_case = container.delete_task_groups_use_case()
        delete_task_use_case = container.delete_task_use_case()
        add_tasks_to_group_use_case = container.add_tasks_to_group_use_case()
        remove_task_from_group_use_case = container.remove_task_from_group_use_case()
        bulk_create_group_use_case = (
            container.bulk_create_group_from_tasks_use_case()
        )
        bulk_add_tasks_to_group_use_case = (
            container.bulk_add_tasks_to_group_use_case()
        )
        bulk_remove_tasks_from_groups_use_case = (
            container.bulk_remove_tasks_from_groups_use_case()
        )
        bulk_delete_variants_use_case = container.bulk_delete_variants_use_case()
        render_work_document_use_case = container.render_work_document_use_case()
        legacy_generate_work_document_use_case = (
            container.generate_work_document_use_case()
        )
        render_remedial_sheet_use_case = (
            container.render_remedial_sheet_document_use_case()
        )
        legacy_generate_remedial_sheet_use_case = (
            container.generate_remedial_sheet_document_use_case()
        )
        rendered_file_use_case = container.get_rendered_document_file_use_case()
        legacy_generated_file_use_case = (
            container.get_generated_document_file_use_case()
        )

        self.assertIsInstance(use_case, CreateRemedialFromEventUseCase)
        self.assertIsInstance(wizard_create_use_case, CreateRemedialWizardWorkUseCase)
        self.assertIsInstance(preview_use_case, GetRemedialEventPreviewUseCase)
        self.assertIsInstance(create_event_use_case, CreateEventUseCase)
        self.assertIsInstance(update_event_use_case, UpdateEventUseCase)
        self.assertIsInstance(
            wizard_preview_use_case,
            GetRemedialWizardPreviewUseCase,
        )
        self.assertIsInstance(
            wizard_start_use_case,
            GetRemedialWizardStartUseCase,
        )
        self.assertIsInstance(profile_use_case, GetStudentProfileUseCase)
        self.assertIsInstance(task_list_use_case, GetTaskListUseCase)
        self.assertIsInstance(task_detail_use_case, GetTaskDetailUseCase)
        self.assertIsInstance(subtopic_options_use_case, GetSubtopicOptionsUseCase)
        self.assertIsInstance(codifier_elements_use_case, GetCodifierElementsUseCase)
        self.assertIsInstance(source_list_use_case, GetSourceListUseCase)
        self.assertIsInstance(
            document_template_list_use_case,
            GetDocumentTemplateListUseCase,
        )
        self.assertIsInstance(
            default_document_template_use_case,
            GetDefaultDocumentTemplateUseCase,
        )
        self.assertIsInstance(
            refresh_math_cache_use_case,
            RefreshTaskMathCacheUseCase,
        )
        self.assertIsInstance(create_task_use_case, CreateTaskUseCase)
        self.assertIsInstance(update_task_use_case, UpdateTaskUseCase)
        self.assertIsInstance(save_task_images_use_case, SaveTaskImagesUseCase)
        self.assertIsInstance(student_detail_use_case, GetStudentDetailUseCase)
        self.assertIsInstance(
            student_group_detail_use_case,
            GetStudentGroupDetailUseCase,
        )
        self.assertIsInstance(student_list_use_case, GetStudentListUseCase)
        self.assertIsInstance(
            student_group_list_use_case,
            GetStudentGroupListUseCase,
        )
        self.assertIsInstance(
            student_remedial_use_case,
            GetStudentRemedialWorkUseCase,
        )
        self.assertIsInstance(create_student_use_case, CreateStudentUseCase)
        self.assertIsInstance(update_student_use_case, UpdateStudentUseCase)
        self.assertIsInstance(
            create_student_group_use_case,
            CreateStudentGroupUseCase,
        )
        self.assertIsInstance(
            update_student_group_use_case,
            UpdateStudentGroupUseCase,
        )
        self.assertIsInstance(
            create_student_remedial_use_case,
            CreateStudentRemedialVariantUseCase,
        )
        self.assertIsInstance(grade_use_case, GradeStudentWorkUseCase)
        self.assertIsInstance(review_use_case, GetParticipationReviewUseCase)
        self.assertIsInstance(dashboard_use_case, GetReviewDashboardUseCase)
        self.assertIsInstance(event_review_use_case, GetEventReviewUseCase)
        self.assertIsInstance(event_list_use_case, GetEventListUseCase)
        self.assertIsInstance(event_detail_use_case, GetEventDetailUseCase)
        self.assertIsInstance(task_group_detail_use_case, GetTaskGroupDetailUseCase)
        self.assertIsInstance(task_group_list_use_case, GetTaskGroupListUseCase)
        self.assertIsInstance(
            create_analog_group_use_case,
            CreateAnalogGroupUseCase,
        )
        self.assertIsInstance(
            update_analog_group_use_case,
            UpdateAnalogGroupUseCase,
        )
        self.assertIsInstance(add_tasks_form_use_case, GetAddTasksToGroupUseCase)
        self.assertIsInstance(course_detail_use_case, GetCourseDetailUseCase)
        self.assertIsInstance(course_list_use_case, GetCourseListUseCase)
        self.assertIsInstance(topic_subtopics_use_case, GetTopicSubtopicsUseCase)
        self.assertIsInstance(topic_list_use_case, GetTopicListUseCase)
        self.assertIsInstance(topic_detail_use_case, GetTopicDetailUseCase)
        self.assertIsInstance(codifier_list_use_case, GetCodifierListUseCase)
        self.assertIsInstance(codifier_detail_use_case, GetCodifierDetailUseCase)
        self.assertIsInstance(dashboard_summary_use_case, GetDashboardSummaryUseCase)
        self.assertIsInstance(global_search_use_case, GetGlobalSearchUseCase)
        self.assertIsInstance(
            heatmap_course_overview_use_case,
            GetHeatmapCourseOverviewUseCase,
        )
        self.assertIsInstance(
            heatmap_course_topic_matrix_use_case,
            GetHeatmapCourseTopicMatrixUseCase,
        )
        self.assertIsInstance(
            heatmap_course_timeline_use_case,
            GetHeatmapCourseTimelineUseCase,
        )
        self.assertIsInstance(
            heatmap_drilldown_overview_use_case,
            GetHeatmapDrilldownOverviewUseCase,
        )
        self.assertIsInstance(
            heatmap_student_detail_use_case,
            GetHeatmapStudentDetailUseCase,
        )
        self.assertIsInstance(
            heatmap_subtopic_detail_use_case,
            GetHeatmapSubtopicDetailUseCase,
        )
        self.assertIsInstance(heatmap_overview_use_case, GetHeatmapOverviewUseCase)
        self.assertIsInstance(
            heatmap_subtopic_matrix_use_case,
            GetHeatmapSubtopicMatrixUseCase,
        )
        self.assertIsInstance(
            heatmap_topic_matrix_use_case,
            GetHeatmapTopicMatrixUseCase,
        )
        self.assertIsInstance(import_page_use_case, GetImportPageUseCase)
        self.assertIsInstance(import_history_use_case, GetImportHistoryUseCase)
        self.assertIsInstance(site_settings_use_case, GetSiteSettingsUseCase)
        self.assertIsInstance(
            save_site_settings_use_case,
            SaveSiteSettingsUseCase,
        )
        self.assertIsInstance(
            import_validation_use_case,
            ValidateTaskImportJsonUseCase,
        )
        self.assertIsInstance(execute_import_use_case, ExecuteTaskImportUseCase)
        self.assertIsInstance(preview_import_use_case, PreviewTaskImportUseCase)
        self.assertIsInstance(sample_import_use_case, GetTaskImportSampleUseCase)
        self.assertIsInstance(export_tasks_use_case, ExportTasksUseCase)
        self.assertIsInstance(create_source_use_case, CreateSourceUseCase)
        self.assertIsInstance(
            participant_selection_use_case,
            GetEventParticipantSelectionUseCase,
        )
        self.assertIsInstance(
            participation_ref_use_case,
            GetEventParticipationRefUseCase,
        )
        self.assertIsInstance(
            variant_assignment_use_case,
            GetEventVariantAssignmentUseCase,
        )
        self.assertIsInstance(
            events_status_report_use_case,
            GetEventsStatusReportUseCase,
        )
        self.assertIsInstance(
            reports_dashboard_use_case,
            GetReportsDashboardUseCase,
        )
        self.assertIsInstance(
            work_analysis_report_use_case,
            GetWorkAnalysisReportUseCase,
        )
        self.assertIsInstance(
            student_performance_report_use_case,
            GetStudentPerformanceReportUseCase,
        )
        self.assertIsInstance(journal_select_use_case, GetJournalSelectUseCase)
        self.assertIsInstance(journal_use_case, GetJournalUseCase)
        self.assertIsInstance(task_db_health_use_case, GetTaskDBHealthUseCase)
        self.assertIsInstance(add_participants_use_case, AddEventParticipantsUseCase)
        self.assertIsInstance(assign_variants_use_case, AssignEventVariantsUseCase)
        self.assertIsInstance(
            assign_single_variant_use_case,
            AssignSingleEventVariantUseCase,
        )
        self.assertIsInstance(change_status_use_case, ChangeEventStatusUseCase)
        self.assertIsInstance(calculate_score_use_case, CalculateReviewScoreUseCase)
        self.assertIsInstance(finalize_event_use_case, FinalizeReviewEventUseCase)
        self.assertIsInstance(toggle_absent_use_case, ToggleParticipationAbsentUseCase)
        self.assertIsInstance(
            prepare_submission_use_case,
            PrepareParticipationReviewSubmissionUseCase,
        )
        self.assertIsInstance(validate_scan_use_case, ValidateReviewWorkScanUseCase)
        self.assertIsInstance(save_navigation_use_case, GetReviewSaveNavigationUseCase)
        self.assertIsInstance(recent_sessions_use_case, GetRecentReviewSessionsUseCase)
        self.assertIsInstance(sync_session_use_case, SyncReviewSessionUseCase)
        self.assertIsInstance(work_detail_use_case, GetWorkDetailUseCase)
        self.assertIsInstance(work_form_data_use_case, GetWorkFormDataUseCase)
        self.assertIsInstance(work_list_use_case, GetWorkListUseCase)
        self.assertIsInstance(variant_detail_use_case, GetVariantDetailUseCase)
        self.assertIsInstance(
            variant_generation_use_case,
            GetVariantGenerationPlaceholderUseCase,
        )
        self.assertIsInstance(
            variant_generation_form_use_case,
            GetVariantGenerationFormUseCase,
        )
        self.assertIsInstance(variant_list_use_case, GetVariantListUseCase)
        self.assertIsInstance(
            orphan_variant_list_use_case,
            GetOrphanVariantListUseCase,
        )
        self.assertIsInstance(sync_work_groups_use_case, SyncWorkAnalogGroupsUseCase)
        self.assertIsInstance(compose_variants_use_case, ComposeWorkVariantsUseCase)
        self.assertIsInstance(generate_variants_use_case, GenerateWorkVariantsUseCase)
        self.assertIsInstance(
            create_from_orphans_use_case,
            CreateWorkFromOrphansUseCase,
        )
        self.assertIsInstance(create_from_groups_use_case, CreateWorkFromGroupsUseCase)
        self.assertIsInstance(create_from_tasks_use_case, CreateWorkFromTasksUseCase)
        self.assertIsInstance(create_work_use_case, CreateWorkUseCase)
        self.assertIsInstance(update_work_use_case, UpdateWorkUseCase)
        self.assertIsInstance(
            save_work_specification_use_case,
            SaveWorkSpecificationUseCase,
        )
        self.assertIsInstance(variant_delete_info_use_case, GetVariantDeleteInfoUseCase)
        self.assertIsInstance(delete_variant_use_case, DeleteVariantUseCase)
        self.assertIsInstance(delete_task_groups_use_case, DeleteTaskGroupsUseCase)
        self.assertIsInstance(delete_task_use_case, DeleteTaskUseCase)
        self.assertIsInstance(add_tasks_to_group_use_case, AddTasksToGroupUseCase)
        self.assertIsInstance(
            remove_task_from_group_use_case,
            RemoveTaskFromGroupUseCase,
        )
        self.assertIsInstance(
            bulk_create_group_use_case,
            BulkCreateGroupFromTasksUseCase,
        )
        self.assertIsInstance(
            bulk_add_tasks_to_group_use_case,
            BulkAddTasksToGroupUseCase,
        )
        self.assertIsInstance(
            bulk_remove_tasks_from_groups_use_case,
            BulkRemoveTasksFromGroupsUseCase,
        )
        self.assertIsInstance(bulk_delete_variants_use_case, BulkDeleteVariantsUseCase)
        self.assertIsInstance(
            render_work_document_use_case,
            RenderWorkDocumentUseCase,
        )
        self.assertIsInstance(
            legacy_generate_work_document_use_case,
            RenderWorkDocumentUseCase,
        )
        self.assertIsInstance(
            render_remedial_sheet_use_case,
            RenderRemedialSheetDocumentUseCase,
        )
        self.assertIsInstance(
            legacy_generate_remedial_sheet_use_case,
            RenderRemedialSheetDocumentUseCase,
        )
        self.assertIsInstance(rendered_file_use_case, GetRenderedDocumentFileUseCase)
        self.assertIsInstance(
            legacy_generated_file_use_case,
            GetRenderedDocumentFileUseCase,
        )
        self.assertIs(GetGeneratedDocumentFileUseCase, GetRenderedDocumentFileUseCase)
        self.assertIsInstance(container.student_repo, DjangoStudentRepository)
        self.assertIsInstance(container.task_repo, DjangoTaskRepository)
        self.assertIsInstance(container.work_repo, DjangoWorkRepository)
        self.assertIsInstance(container.event_repo, DjangoEventRepository)
        self.assertIsInstance(container.review_repo, DjangoReviewRepository)
        self.assertIsInstance(container.report_repo, DjangoReportRepository)
        self.assertIsInstance(container.curriculum_repo, DjangoCurriculumRepository)
        self.assertIsInstance(container.codifier_repo, DjangoCodifierRepository)
        self.assertIsInstance(container.core_repo, DjangoCoreRepository)
        self.assertIsInstance(container.settings_repo, DjangoSettingsRepository)
        self.assertIsInstance(
            container.document_template_repo,
            DjangoDocumentTemplateRepository,
        )
        self.assertIsInstance(container.core_form_adapter, CoreFormAdapter)
        self.assertIsInstance(container.report_form_adapter, ReportFormAdapter)
        self.assertIsInstance(container.task_form_adapter, TaskFormAdapter)
        self.assertIsInstance(container.work_form_adapter, WorkFormAdapter)
        self.assertIsInstance(
            container.document_engine,
            DjangoDocumentEngine,
        )
        self.assertIs(
            container.document_rendering_service,
            container.document_engine,
        )
        self.assertIs(
            container.document_generation_service,
            container.document_engine,
        )
        self.assertIsInstance(container.task_import_service, DjangoTaskImportService)
