from django.test import SimpleTestCase

from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from infrastructure.container import Container
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository


class ContainerTests(SimpleTestCase):
    def test_wires_remedial_from_event_use_case(self):
        container = Container()

        use_case = container.create_remedial_from_event_use_case()
        preview_use_case = container.get_remedial_event_preview_use_case()
        profile_use_case = container.get_student_profile_use_case()

        self.assertIsInstance(use_case, CreateRemedialFromEventUseCase)
        self.assertIsInstance(preview_use_case, GetRemedialEventPreviewUseCase)
        self.assertIsInstance(profile_use_case, GetStudentProfileUseCase)
        self.assertIsInstance(container.student_repo, DjangoStudentRepository)
        self.assertIsInstance(container.task_repo, DjangoTaskRepository)
        self.assertIsInstance(container.work_repo, DjangoWorkRepository)
        self.assertIsInstance(container.event_repo, DjangoEventRepository)
