"""Django read adapter for student catalog and detail data."""

from core_logic.entities.student import (
    StudentDetail,
    StudentGroupRef,
    StudentListItem,
)
from core_logic.interfaces.student_catalog_repo import IStudentCatalogRepository
from students.models import Student, StudentGroup


class DjangoStudentCatalogRepository(IStudentCatalogRepository):
    def get_list_students(self, year=None):
        students = Student.objects.all()
        if year:
            students = students.filter(
                studentgroup__academic_year_id=year.pk,
            ).distinct()
        return tuple(
            StudentListItem(
                pk=str(student.pk),
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
                email=student.email,
                created_at=student.created_at,
            )
            for student in students.order_by('last_name', 'first_name')
        )

    def get_student(self, student_id: str):
        student = Student.objects.filter(pk=student_id).first()
        if student is None:
            return None
        return StudentDetail(
            pk=str(student.pk),
            first_name=student.first_name,
            last_name=student.last_name,
            middle_name=student.middle_name,
            email=student.email,
            short_uuid=student.get_short_uuid(),
            full_name=student.get_full_name(),
            short_name=student.get_short_name(),
        )

    def get_student_groups(self, student_id: str):
        return tuple(
            StudentGroupRef(pk=str(group.pk), name=group.name)
            for group in StudentGroup.objects.filter(
                students__id=student_id,
            ).order_by('name')
        )
