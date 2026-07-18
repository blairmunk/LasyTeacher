"""Infrastructure helpers for Django event forms."""

from django.utils import timezone

from core_logic.interfaces.event_repo import CreateEventParams
from core_logic.use_cases.grade_student_work import GradeStudentWorkRequest


class EventFormAdapter:
    def event_params_from_form(self, form, event_id=''):
        course = form.cleaned_data.get('course')
        return CreateEventParams(
            event_id=event_id,
            name=form.cleaned_data['name'],
            work_id=str(form.cleaned_data['work'].pk),
            date=form.cleaned_data['planned_date'],
            status=form.cleaned_data.get('status', 'planned'),
            course_id=str(course.pk) if course else None,
            location=form.cleaned_data.get('location', ''),
            description=form.cleaned_data.get('description', ''),
        )

    def event_form_initial(self, event):
        planned_date = event.planned_date
        if planned_date:
            planned_date = timezone.localtime(planned_date).date()
        return {
            'name': event.name,
            'work': event.work_id,
            'planned_date': planned_date,
            'status': event.status,
            'course': event.course_id,
            'description': event.description,
            'location': event.location,
        }

    def selected_student_ids_from_form(self, form):
        students = []
        cleaned_data = form.cleaned_data
        if cleaned_data.get('student_group'):
            students.extend(cleaned_data['student_group'].students.all())
        if cleaned_data.get('individual_students'):
            students.extend(cleaned_data['individual_students'])
        return [str(student.pk) for student in students]

    def assignments_from_form(self, form):
        assignments = {}
        for field_name, variant_id in form.cleaned_data.items():
            if not field_name.startswith('variant_') or not variant_id:
                continue
            assignments[field_name.removeprefix('variant_')] = variant_id
        return assignments

    def grade_student_work_request_from_form(
        self,
        form,
        participation_id,
        checked_by_display_name='',
        checked_by_username='',
        sync_event_status=True,
    ):
        data = form.cleaned_data
        return GradeStudentWorkRequest(
            participation_id=participation_id,
            score=data.get('score'),
            points=data.get('points'),
            max_points=data.get('max_points'),
            teacher_comment=data.get('teacher_comment', ''),
            mistakes_analysis=data.get('mistakes_analysis', ''),
            recommendations=data.get('recommendations', ''),
            checked_by_display_name=checked_by_display_name,
            checked_by_username=checked_by_username,
            work_scan=data.get('work_scan'),
            is_retake=data.get('is_retake', False),
            is_excellent=data.get('is_excellent', False),
            needs_attention=data.get('needs_attention', False),
            sync_event_status=sync_event_status,
        )
