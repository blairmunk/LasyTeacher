"""Django snapshot adapter for planning student imports."""

from core.models import AcademicYear
from core_logic.entities.student_import import (
    StudentImportAcademicYearRef,
    StudentImportGroupRef,
    StudentImportMembershipRef,
    StudentImportSnapshot,
    StudentImportStudentRef,
)
from core_logic.interfaces.student_import_snapshot_repo import (
    IStudentImportSnapshotRepository,
)
from students.models import Student, StudentGroup


class DjangoStudentImportSnapshotRepository(
    IStudentImportSnapshotRepository,
):
    def get_student_import_snapshot(self) -> StudentImportSnapshot:
        return StudentImportSnapshot(
            academic_years=tuple(
                StudentImportAcademicYearRef(
                    pk=str(year.pk),
                    name=year.name,
                    is_active=year.is_active,
                )
                for year in AcademicYear.objects.all()
            ),
            groups=tuple(
                StudentImportGroupRef(
                    pk=str(group.pk),
                    name=group.name,
                    academic_year_name=(
                        group.academic_year.name
                        if group.academic_year
                        else ''
                    ),
                )
                for group in StudentGroup.objects.select_related(
                    'academic_year',
                )
            ),
            students=tuple(
                StudentImportStudentRef(
                    pk=str(student.pk),
                    last_name=student.last_name,
                    first_name=student.first_name,
                    middle_name=student.middle_name,
                    email=student.email,
                )
                for student in Student.objects.all()
            ),
            memberships=tuple(
                StudentImportMembershipRef(
                    group_id=str(group_id),
                    student_id=str(student_id),
                )
                for group_id, student_id in (
                    StudentGroup.students.through.objects.values_list(
                        'studentgroup_id',
                        'student_id',
                    )
                )
            ),
        )
