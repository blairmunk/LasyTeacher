"""Infrastructure helpers for Django student forms."""

from core_logic.entities.student import SaveStudentGroupParams, SaveStudentParams


class StudentFormAdapter:
    def student_params_from_form(self, form, student_id=''):
        return SaveStudentParams(
            student_id=student_id,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            middle_name=form.cleaned_data.get('middle_name', ''),
            email=form.cleaned_data.get('email', ''),
        )

    def student_form_initial(self, student):
        return {
            'first_name': student.first_name,
            'last_name': student.last_name,
            'middle_name': student.middle_name,
            'email': student.email,
        }

    def student_group_params_from_form(self, form, group_id=''):
        return SaveStudentGroupParams(
            group_id=group_id,
            name=form.cleaned_data['name'],
            student_ids=[
                str(student.pk)
                for student in form.cleaned_data.get('students', [])
            ],
        )

    def student_group_form_initial(self, group):
        return {
            'name': group.name,
            'students': [student.pk for student in group.students],
        }
