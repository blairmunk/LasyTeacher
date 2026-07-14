from django.test import SimpleTestCase

from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
from core_logic.use_cases.assign_event_variants import AssignEventVariantsUseCase
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.calculate_review_score import CalculateReviewScoreUseCase
from core_logic.use_cases.change_event_status import ChangeEventStatusUseCase
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
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
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentUseCase,
)
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
        self.assertIsInstance(container.student_repo, DjangoStudentRepository)
        self.assertIsInstance(container.task_repo, DjangoTaskRepository)
        self.assertIsInstance(container.work_repo, DjangoWorkRepository)
        self.assertIsInstance(container.event_repo, DjangoEventRepository)
        self.assertIsInstance(container.review_repo, DjangoReviewRepository)
