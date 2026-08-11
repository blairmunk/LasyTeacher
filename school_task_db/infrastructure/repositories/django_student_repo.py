"""Django implementation of the student repository."""

from typing import List

from django.db.models import Count

from core_logic.entities.student import (
    SaveStudentGroupParams,
    SaveStudentGroupResult,
    SaveStudentParams,
    SaveStudentResult,
    StudentDetail,
    StudentGroupDetail,
    StudentGroupDetailStudent,
    StudentGroupListItem,
    StudentGroupRef,
    StudentListItem,
)
from core_logic.interfaces.student_repo import IStudentRepository
from students.models import Student, StudentGroup


class DjangoStudentRepository(IStudentRepository):
    @staticmethod
    def _student_detail(student):
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

    def get_list_students(self, year=None):
        students = Student.objects.all()
        if year:
            students = students.filter(
                studentgroup__academic_year_id=year.pk,
            ).distinct()
        return [
            StudentListItem(
                pk=str(student.pk),
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
                email=student.email,
                created_at=student.created_at,
            )
            for student in students.order_by('last_name', 'first_name')
        ]

    def get_list_student_groups(self, year=None):
        groups = StudentGroup.objects.select_related('academic_year')
        if year:
            groups = groups.filter(academic_year_id=year.pk)
        return [
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
        ]

    def get_student(self, student_id: str):
        student = Student.objects.filter(pk=student_id).first()
        if student is None:
            return None
        return self._student_detail(student)

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
            students=[
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
            ],
        )

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

    def get_student_groups(self, student_id: str) -> List[StudentGroupRef]:
        return [
            StudentGroupRef(pk=str(group.pk), name=group.name)
            for group in StudentGroup.objects.filter(
                students__id=student_id,
            ).order_by('name')
        ]

    def get_all_student_groups(self) -> List[StudentGroupRef]:
        return [
            StudentGroupRef(pk=str(group.pk), name=str(group))
            for group in StudentGroup.objects.select_related(
                'academic_year',
            ).order_by('name')
        ]

    def get_group_name(self, group_id: str):
        group = StudentGroup.objects.filter(pk=group_id).first()
        return group.name if group else None
