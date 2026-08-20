"""Event workflow wiring for the application dependency container."""

from core_logic.services.event_service import EventService
from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
from core_logic.use_cases.assign_event_variants import AssignEventVariantsUseCase
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.change_event_status import ChangeEventStatusUseCase
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
from core_logic.use_cases.prepare_event_action_submission import (
    PrepareAssignSingleVariantSubmissionUseCase,
    PrepareChangeEventStatusSubmissionUseCase,
)
from core_logic.use_cases.save_event import CreateEventUseCase, UpdateEventUseCase
from infrastructure.forms.event_forms import EventFormAdapter
from infrastructure.repositories.django_event_attempt_repo import (
    DjangoEventAttemptRepository,
)
from infrastructure.repositories.django_event_participation_repo import (
    DjangoEventParticipationRepository,
)
from infrastructure.repositories.django_event_read_repo import (
    DjangoEventReadRepository,
)
from infrastructure.repositories.django_event_write_repo import (
    DjangoEventWriteRepository,
)


class EventCompositionMixin:
    """Owns event planning, participation, and status infrastructure wiring."""

    def _initialize_event_composition(self):
        self._event_read_repo = None
        self._event_write_repo = None
        self._event_participation_repo = None
        self._event_attempt_repo = None
        self._event_form_adapter = None

    @property
    def event_read_repo(self):
        if self._event_read_repo is None:
            self._event_read_repo = DjangoEventReadRepository()
        return self._event_read_repo

    @property
    def event_write_repo(self):
        if self._event_write_repo is None:
            self._event_write_repo = DjangoEventWriteRepository()
        return self._event_write_repo

    @property
    def event_participation_repo(self):
        if self._event_participation_repo is None:
            self._event_participation_repo = (
                DjangoEventParticipationRepository()
            )
        return self._event_participation_repo

    @property
    def event_attempt_repo(self):
        if self._event_attempt_repo is None:
            self._event_attempt_repo = DjangoEventAttemptRepository()
        return self._event_attempt_repo

    @property
    def event_form_adapter(self):
        if self._event_form_adapter is None:
            self._event_form_adapter = EventFormAdapter()
        return self._event_form_adapter

    def event_service(self):
        return EventService()

    def create_event_use_case(self):
        return CreateEventUseCase(
            event_repo=self.event_write_repo,
        )

    def update_event_use_case(self):
        return UpdateEventUseCase(
            event_repo=self.event_write_repo,
        )

    def get_event_list_use_case(self):
        return GetEventListUseCase(
            event_repo=self.event_read_repo,
            event_service=self.event_service(),
        )

    def get_event_detail_use_case(self):
        return GetEventDetailUseCase(
            event_repo=self.event_read_repo,
            event_service=self.event_service(),
        )

    def get_event_participant_selection_use_case(self):
        return GetEventParticipantSelectionUseCase(
            event_repo=self.event_read_repo,
        )

    def get_event_participation_ref_use_case(self):
        return GetEventParticipationRefUseCase(
            event_repo=self.event_read_repo,
        )

    def get_event_variant_assignment_use_case(self):
        return GetEventVariantAssignmentUseCase(
            event_repo=self.event_read_repo,
        )

    def add_event_participants_use_case(self):
        return AddEventParticipantsUseCase(
            event_repo=self.event_participation_repo,
        )

    def assign_event_variants_use_case(self):
        return AssignEventVariantsUseCase(
            event_repo=self.event_read_repo,
            event_participation_repo=self.event_participation_repo,
        )

    def assign_single_event_variant_use_case(self):
        return AssignSingleEventVariantUseCase(
            event_repo=self.event_read_repo,
            event_participation_repo=self.event_participation_repo,
        )

    def change_event_status_use_case(self):
        return ChangeEventStatusUseCase(
            event_repo=self.event_read_repo,
            event_write_repo=self.event_write_repo,
            event_service=self.event_service(),
        )

    def prepare_assign_single_variant_submission_use_case(self):
        return PrepareAssignSingleVariantSubmissionUseCase()

    def prepare_change_event_status_submission_use_case(self):
        return PrepareChangeEventStatusSubmissionUseCase()
