"""Django command adapter for student records."""

from core_logic.entities.student import SaveStudentParams, SaveStudentResult
from core_logic.interfaces.student_command_repo import IStudentCommandRepository
from students.models import Student


class DjangoStudentCommandRepository(IStudentCommandRepository):
    def create_student(self, params: SaveStudentParams) -> SaveStudentResult:
        student = Student.objects.create(
            first_name=params.first_name,
            last_name=params.last_name,
            middle_name=params.middle_name,
            email=params.email,
        )
        return SaveStudentResult(status='created', student_id=str(student.pk))

    def update_student(self, params: SaveStudentParams) -> SaveStudentResult:
        student = Student.objects.filter(pk=params.student_id).first()
        if student is None:
            return SaveStudentResult(status='not_found')

        student.first_name = params.first_name
        student.last_name = params.last_name
        student.middle_name = params.middle_name
        student.email = params.email
        student.save()
        return SaveStudentResult(status='updated', student_id=str(student.pk))
