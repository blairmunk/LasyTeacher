"""Infrastructure helpers for Django event forms."""

from django.utils import timezone

from core_logic.interfaces.event_repo import CreateEventParams


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
