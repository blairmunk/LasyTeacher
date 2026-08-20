"""Application dependency composition root."""

from infrastructure.containers.application import ApplicationCompositionMixin
from infrastructure.containers.curriculum import CurriculumCompositionMixin
from infrastructure.containers.document import DocumentCompositionMixin
from infrastructure.containers.event import EventCompositionMixin
from infrastructure.containers.remedial import RemedialCompositionMixin
from infrastructure.containers.reporting import ReportingCompositionMixin
from infrastructure.containers.review import ReviewCompositionMixin
from infrastructure.containers.student import StudentCompositionMixin
from infrastructure.containers.task import TaskCompositionMixin
from infrastructure.containers.work import WorkCompositionMixin
from infrastructure.services.django_transaction_manager import (
    DjangoTransactionManager,
)


class Container(
    ApplicationCompositionMixin,
    CurriculumCompositionMixin,
    DocumentCompositionMixin,
    EventCompositionMixin,
    RemedialCompositionMixin,
    ReportingCompositionMixin,
    ReviewCompositionMixin,
    StudentCompositionMixin,
    TaskCompositionMixin,
    WorkCompositionMixin,
):
    """Wires pure use cases to infrastructure adapters."""

    def __init__(self):
        self._initialize_application_composition()
        self._initialize_curriculum_composition()
        self._initialize_document_composition()
        self._initialize_event_composition()
        self._initialize_remedial_composition()
        self._initialize_reporting_composition()
        self._initialize_review_composition()
        self._initialize_student_composition()
        self._initialize_task_composition()
        self._initialize_work_composition()
        self._transaction_manager = None

    @property
    def transaction_manager(self):
        if self._transaction_manager is None:
            self._transaction_manager = DjangoTransactionManager()
        return self._transaction_manager


container = Container()
