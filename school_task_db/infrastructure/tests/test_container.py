from django.test import SimpleTestCase

from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
from core_logic.use_cases.assign_event_variants import AssignEventVariantsUseCase
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsUseCase
from core_logic.use_cases.calculate_review_score import CalculateReviewScoreUseCase
from core_logic.use_cases.change_event_status import ChangeEventStatusUseCase
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansUseCase,
)
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
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_recent_review_sessions import (
    GetRecentReviewSessionsUseCase,
)
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionUseCase,
)
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


class ContainerTests(SimpleTestCase):
    def test_wires_remedial_from_event_use_case(self):
        container = Container()

        use_case = container.create_remedial_from_event_use_case()
        preview_use_case = container.get_remedial_event_preview_use_case()
        profile_use_case = container.get_student_profile_use_case()
        grade_use_case = container.grade_student_work_use_case()
        review_use_case = container.get_participation_review_use_case()
        dashboard_use_case = container.get_review_dashboard_use_case()
        event_review_use_case = container.get_event_review_use_case()
        event_list_use_case = container.get_event_list_use_case()
        event_detail_use_case = container.get_event_detail_use_case()
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
        sync_work_groups_use_case = container.sync_work_analog_groups_use_case()
        generate_variants_use_case = container.generate_work_variants_use_case()
        create_from_orphans_use_case = container.create_work_from_orphans_use_case()
        variant_delete_info_use_case = container.get_variant_delete_info_use_case()
        delete_variant_use_case = container.delete_variant_use_case()
        bulk_delete_variants_use_case = container.bulk_delete_variants_use_case()

        self.assertIsInstance(use_case, CreateRemedialFromEventUseCase)
        self.assertIsInstance(preview_use_case, GetRemedialEventPreviewUseCase)
        self.assertIsInstance(profile_use_case, GetStudentProfileUseCase)
        self.assertIsInstance(grade_use_case, GradeStudentWorkUseCase)
        self.assertIsInstance(review_use_case, GetParticipationReviewUseCase)
        self.assertIsInstance(dashboard_use_case, GetReviewDashboardUseCase)
        self.assertIsInstance(event_review_use_case, GetEventReviewUseCase)
        self.assertIsInstance(event_list_use_case, GetEventListUseCase)
        self.assertIsInstance(event_detail_use_case, GetEventDetailUseCase)
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
        self.assertIsInstance(sync_work_groups_use_case, SyncWorkAnalogGroupsUseCase)
        self.assertIsInstance(generate_variants_use_case, GenerateWorkVariantsUseCase)
        self.assertIsInstance(create_from_orphans_use_case, CreateWorkFromOrphansUseCase)
        self.assertIsInstance(variant_delete_info_use_case, GetVariantDeleteInfoUseCase)
        self.assertIsInstance(delete_variant_use_case, DeleteVariantUseCase)
        self.assertIsInstance(bulk_delete_variants_use_case, BulkDeleteVariantsUseCase)
        self.assertIsInstance(container.student_repo, DjangoStudentRepository)
        self.assertIsInstance(container.task_repo, DjangoTaskRepository)
        self.assertIsInstance(container.work_repo, DjangoWorkRepository)
        self.assertIsInstance(container.event_repo, DjangoEventRepository)
        self.assertIsInstance(container.review_repo, DjangoReviewRepository)
