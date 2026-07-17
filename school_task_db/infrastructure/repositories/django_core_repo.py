"""Django implementation of the core repository."""

from core_logic.interfaces.core_repo import ICoreRepository
from events.models import Event
from students.models import Student
from task_groups.models import AnalogGroup
from tasks.models import Task
from works.models import Variant, Work


class DjangoCoreRepository(ICoreRepository):
    def count_tasks(self) -> int:
        return Task.objects.count()

    def count_works(self) -> int:
        return Work.objects.count()

    def count_variants(self) -> int:
        return Variant.objects.count()

    def count_orphan_variants(self) -> int:
        return Variant.objects.filter(work__isnull=True).count()

    def count_students(self) -> int:
        return Student.objects.count()

    def count_events(self) -> int:
        return Event.objects.count()

    def count_analog_groups(self) -> int:
        return AnalogGroup.objects.count()
