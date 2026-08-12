"""Django command adapter for applying planned student imports."""

from core.models import AcademicYear
from core_logic.entities.student_import import StudentImportPlan
from core_logic.interfaces.student_import_command_repo import (
    IStudentImportCommandRepository,
)
from students.models import Student, StudentGroup


class DjangoStudentImportCommandRepository(
    IStudentImportCommandRepository,
):
    def apply_student_import_plan(self, plan: StudentImportPlan) -> None:
        years_by_name = {
            year.name: year
            for year in AcademicYear.objects.filter(
                name__in=[item.name for item in plan.academic_years_to_create],
            )
        }
        for item in plan.academic_years_to_create:
            if item.name not in years_by_name:
                years_by_name[item.name] = AcademicYear.objects.create(
                    name=item.name,
                    start_date=item.start_date,
                    end_date=item.end_date,
                    is_active=item.is_active,
                )

        group_ids = {}
        for item in plan.groups_to_create:
            academic_year = (
                years_by_name.get(item.academic_year_name)
                or AcademicYear.objects.filter(
                    name=item.academic_year_name,
                ).first()
                if item.academic_year_name
                else None
            )
            group = StudentGroup.objects.create(
                name=item.name,
                academic_year=academic_year,
            )
            group_ids[item.token] = str(group.pk)

        student_ids = {}
        for item in plan.student_mutations:
            if item.operation == 'create':
                student = Student.objects.create(
                    last_name=item.last_name,
                    first_name=item.first_name,
                    middle_name=item.middle_name,
                    email=item.email,
                )
                student_ids[item.token] = str(student.pk)
                continue

            student_id = student_ids.get(item.token) or _existing_id(
                item.token,
            )
            Student.objects.filter(pk=student_id).update(
                last_name=item.last_name,
                first_name=item.first_name,
                middle_name=item.middle_name,
                email=item.email,
            )

        for item in plan.memberships_to_create:
            group_id = group_ids.get(item.group_token) or _existing_id(
                item.group_token,
            )
            student_id = student_ids.get(item.student_token) or _existing_id(
                item.student_token,
            )
            StudentGroup.objects.get(pk=group_id).students.add(student_id)


def _existing_id(token: str) -> str:
    prefix, separator, object_id = token.partition(':')
    if prefix != 'existing' or not separator or not object_id:
        raise ValueError(f'Неизвестный токен плана импорта: {token}')
    return object_id
