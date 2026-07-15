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
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
from core_logic.use_cases.generate_work_variants import GenerateWorkVariantsUseCase
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)
from core_logic.use_cases.get_event_review import GetEventReviewUseCase
from core_logic.use_cases.get_event_detail import GetEventDetailUseCase
from core_logic.use_cases.get_event_list import GetEventListUseCase
from core_logic.use_cases.get_event_participant_selection import (
    GetEventParticipantSelectionUseCase,
)
from core_logic.use_cases.get_event_variant_assignment import (
    GetEventVariantAssignmentUseCase,
)
from core_logic.use_cases.get_generated_document_file import (
    GetGeneratedDocumentFileUseCase,
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
from core_logic.use_cases.get_recent_review_sessions import (
    GetRecentReviewSessionsUseCase,
)
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_list import GetTaskListUseCase
from core_logic.use_cases.get_task_reference_options import (
    GetCodifierElementsUseCase,
    GetSubtopicOptionsUseCase,
)
from core_logic.use_cases.get_source_list import GetSourceListUseCase
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.get_variant_detail import GetVariantDetailUseCase
from core_logic.use_cases.get_variant_generation_placeholder import (
    GetVariantGenerationPlaceholderUseCase,
)
from core_logic.use_cases.get_variant_list import GetVariantListUseCase
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.get_work_form_data import GetWorkFormDataUseCase
from core_logic.use_cases.get_work_list import GetWorkListUseCase
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionUseCase,
)
from core_logic.use_cases.refresh_task_math_cache import RefreshTaskMathCacheUseCase
from core_logic.use_cases.sync_review_session import SyncReviewSessionUseCase
from core_logic.use_cases.sync_work_analog_groups import SyncWorkAnalogGroupsUseCase
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentUseCase,
)
from core_logic.use_cases.validate_review_work_scan import ValidateReviewWorkScanUseCase
from infrastructure.container import Container
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from infrastructure.forms.task_forms import TaskFormAdapter
from infrastructure.forms.work_forms import WorkFormAdapter


class ContainerTests(SimpleTestCase):
    def test_wires_remedial_from_event_use_case(self):
        container = Container()

        use_case = container.create_remedial_from_event_use_case()
        wizard_create_use_case = container.create_remedial_wizard_work_use_case()
        preview_use_case = container.get_remedial_event_preview_use_case()
        wizard_preview_use_case = container.get_remedial_wizard_preview_use_case()
        wizard_start_use_case = container.get_remedial_wizard_start_use_case()
        profile_use_case = container.get_student_profile_use_case()
        task_list_use_case = container.get_task_list_use_case()
        task_detail_use_case = container.get_task_detail_use_case()
        subtopic_options_use_case = container.get_subtopic_options_use_case()
        codifier_elements_use_case = container.get_codifier_elements_use_case()
        source_list_use_case = container.get_source_list_use_case()
        refresh_math_cache_use_case = container.refresh_task_math_cache_use_case()
        student_remedial_use_case = container.get_student_remedial_work_use_case()
        create_student_remedial_use_case = (
            container.create_student_remedial_variant_use_case()
        )
        grade_use_case = container.grade_student_work_use_case()
        review_use_case = container.get_participation_review_use_case()
        dashboard_use_case = container.get_review_dashboard_use_case()
        event_review_use_case = container.get_event_review_use_case()
        event_list_use_case = container.get_event_list_use_case()
        event_detail_use_case = container.get_event_detail_use_case()
        participant_selection_use_case = (
            container.get_event_participant_selection_use_case()
        )
        variant_assignment_use_case = (
            container.get_event_variant_assignment_use_case()
        )
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
        variant_list_use_case = container.get_variant_list_use_case()
        orphan_variant_list_use_case = container.get_orphan_variant_list_use_case()
        sync_work_groups_use_case = container.sync_work_analog_groups_use_case()
        generate_variants_use_case = container.generate_work_variants_use_case()
        create_from_orphans_use_case = container.create_work_from_orphans_use_case()
        create_from_groups_use_case = container.create_work_from_groups_use_case()
        create_from_tasks_use_case = container.create_work_from_tasks_use_case()
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
        generated_file_use_case = container.get_generated_document_file_use_case()

        self.assertIsInstance(use_case, CreateRemedialFromEventUseCase)
        self.assertIsInstance(wizard_create_use_case, CreateRemedialWizardWorkUseCase)
        self.assertIsInstance(preview_use_case, GetRemedialEventPreviewUseCase)
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
            refresh_math_cache_use_case,
            RefreshTaskMathCacheUseCase,
        )
        self.assertIsInstance(
            student_remedial_use_case,
            GetStudentRemedialWorkUseCase,
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
        self.assertIsInstance(
            participant_selection_use_case,
            GetEventParticipantSelectionUseCase,
        )
        self.assertIsInstance(
            variant_assignment_use_case,
            GetEventVariantAssignmentUseCase,
        )
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
        self.assertIsInstance(variant_list_use_case, GetVariantListUseCase)
        self.assertIsInstance(
            orphan_variant_list_use_case,
            GetOrphanVariantListUseCase,
        )
        self.assertIsInstance(sync_work_groups_use_case, SyncWorkAnalogGroupsUseCase)
        self.assertIsInstance(generate_variants_use_case, GenerateWorkVariantsUseCase)
        self.assertIsInstance(create_from_orphans_use_case, CreateWorkFromOrphansUseCase)
        self.assertIsInstance(create_from_groups_use_case, CreateWorkFromGroupsUseCase)
        self.assertIsInstance(create_from_tasks_use_case, CreateWorkFromTasksUseCase)
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
        self.assertIsInstance(generated_file_use_case, GetGeneratedDocumentFileUseCase)
        self.assertIsInstance(container.student_repo, DjangoStudentRepository)
        self.assertIsInstance(container.task_repo, DjangoTaskRepository)
        self.assertIsInstance(container.work_repo, DjangoWorkRepository)
        self.assertIsInstance(container.event_repo, DjangoEventRepository)
        self.assertIsInstance(container.review_repo, DjangoReviewRepository)
        self.assertIsInstance(container.task_form_adapter, TaskFormAdapter)
        self.assertIsInstance(container.work_form_adapter, WorkFormAdapter)
