"""Django command adapter for student groups/classes."""

from core_logic.entities.student import (
    SaveStudentGroupParams,
    SaveStudentGroupResult,
)
from core_logic.interfaces.student_group_command_repo import (
    IStudentGroupCommandRepository,
)
from students.models import StudentGroup


class DjangoStudentGroupCommandRepository(IStudentGroupCommandRepository):
    def create_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        group = StudentGroup.objects.create(name=params.name)
        group.students.set(params.student_ids)
        return SaveStudentGroupResult(status='created', group_id=str(group.pk))

    def update_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        group = StudentGroup.objects.filter(pk=params.group_id).first()
        if group is None:
            return SaveStudentGroupResult(status='not_found')

        group.name = params.name
        group.save()
        group.students.set(params.student_ids)
        return SaveStudentGroupResult(status='updated', group_id=str(group.pk))
