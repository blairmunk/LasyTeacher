"""Django read adapter for student groups/classes."""

from django.db.models import Count

from core_logic.entities.student import (
    StudentGroupDetail,
    StudentGroupDetailStudent,
    StudentGroupListItem,
    StudentGroupRef,
)
from core_logic.interfaces.student_group_catalog_repo import (
    IStudentGroupCatalogRepository,
)
from students.models import StudentGroup


class DjangoStudentGroupCatalogRepository(IStudentGroupCatalogRepository):
    def get_list_student_groups(self, year=None):
        groups = StudentGroup.objects.select_related('academic_year')
        if year:
            groups = groups.filter(academic_year_id=year.pk)
        return tuple(
            StudentGroupListItem(
                pk=str(group.pk),
                name=group.name,
                short_uuid=group.get_short_uuid(),
                created_at=group.created_at,
                students_count=group.students_count,
            )
            for group in groups.annotate(
                students_count=Count('students'),
            ).order_by('name')
        )

    def get_student_group(self, group_id: str):
        group = StudentGroup.objects.select_related(
            'academic_year',
        ).prefetch_related(
            'students',
        ).filter(pk=group_id).first()
        if group is None:
            return None

        return StudentGroupDetail(
            pk=str(group.pk),
            name=group.name,
            short_uuid=group.get_short_uuid(),
            created_at=group.created_at,
            students=tuple(
                StudentGroupDetailStudent(
                    pk=str(student.pk),
                    last_name=student.last_name,
                    first_name=student.first_name,
                    middle_name=student.middle_name,
                    email=student.email,
                    short_uuid=student.get_short_uuid(),
                )
                for student in group.students.all().order_by(
                    'last_name',
                    'first_name',
                )
            ),
        )

    def get_all_student_groups(self):
        return tuple(
            StudentGroupRef(pk=str(group.pk), name=str(group))
            for group in StudentGroup.objects.select_related(
                'academic_year',
            ).order_by('name')
        )

    def get_group_name(self, group_id: str):
        group = StudentGroup.objects.filter(pk=group_id).first()
        return group.name if group else None
