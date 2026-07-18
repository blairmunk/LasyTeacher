from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.http import Http404
from django.utils import timezone

from core_logic.interfaces.event_repo import CreateEventParams
from infrastructure.container import container
from .forms import EventForm, StudentSelectionForm, MarkForm, VariantAssignmentForm


def _post_lists(post_data):
    return {
        key: post_data.getlist(key)
        for key in post_data
    }


def _event_params_from_form(form, event_id=''):
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


def _event_form_initial(event):
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


def _selected_student_ids(cleaned_data):
    students = []
    if cleaned_data.get('student_group'):
        students.extend(cleaned_data['student_group'].students.all())
    if cleaned_data.get('individual_students'):
        students.extend(cleaned_data['individual_students'])
    return [str(student.pk) for student in students]


def _next_or_event_detail(request, event):
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    event_id = getattr(event, 'pk', event)
    return redirect('events:detail', pk=event_id)


class EventListView(TemplateView):
    template_name = 'events/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event_list = container.get_event_list_use_case().execute()
        context['events'] = event_list.events
        context['planned_events'] = event_list.planned_events
        context['active_events'] = event_list.active_events
        context['graded_events'] = event_list.graded_events

        return context



class EventDetailView(TemplateView):
    template_name = 'events/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        detail = container.get_event_detail_use_case().execute(
            event_id=str(self.kwargs['pk']),
        )
        if detail.event is None:
            raise Http404('Событие не найдено')

        context['event'] = detail.event
        context['participations'] = detail.participations
        context['some_variants_assigned'] = detail.some_variants_assigned
        context['all_variants_assigned'] = detail.all_variants_assigned
        context['can_review'] = detail.can_review
        context['status_color'] = detail.status_color
        context['status_steps'] = detail.status_steps
        context['available_variants'] = detail.available_variants
        context['status_transitions'] = detail.status_transitions

        return context


class EventCreateView(TemplateView):
    template_name = 'events/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or EventForm()
        context['page_title'] = 'Создание события'
        context['submit_text'] = 'Создать'
        return context

    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        event_result = container.create_event_use_case().execute(
            _event_params_from_form(form),
        )

        from core_logic.use_cases.add_event_participants import (
            AddEventParticipantsRequest,
        )

        result = container.add_event_participants_use_case().execute(
            AddEventParticipantsRequest(
                event_id=event_result.event_id,
                student_ids=_selected_student_ids(form.cleaned_data),
            )
        )

        if result.created_count:
            messages.success(
                request,
                f'Событие создано, добавлено {result.created_count} учеников'
            )
        else:
            messages.success(request, 'Событие создано')

        return redirect('events:detail', pk=event_result.event_id)


class EventUpdateView(TemplateView):
    template_name = 'events/form.html'

    def _get_event(self):
        detail = container.get_event_detail_use_case().execute(
            event_id=str(self.kwargs['pk']),
        )
        if detail.event is None:
            raise Http404('Событие не найдено')
        return detail.event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = kwargs.get('object') or self._get_event()
        context['object'] = event
        context['form'] = kwargs.get('form') or EventForm(
            initial=_event_form_initial(event),
        )
        context['page_title'] = 'Редактирование события'
        context['submit_text'] = 'Сохранить'
        return context

    def post(self, request, *args, **kwargs):
        event = self._get_event()
        form = EventForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, object=event),
            )

        result = container.update_event_use_case().execute(
            _event_params_from_form(form, event_id=str(event.pk)),
        )
        if result.status == 'not_found':
            raise Http404('Событие не найдено')

        messages.success(request, 'Событие успешно обновлено!')
        return redirect('events:list')


def add_participants(request, event_id):
    """Добавление участников в событие"""
    from infrastructure.container import container

    selection_data = container.get_event_participant_selection_use_case().execute(
        str(event_id),
    )
    if selection_data.status == 'not_found':
        raise Http404("Событие не найдено")
    event = selection_data.event

    if request.method == 'POST':
        form = StudentSelectionForm(request.POST)
        if form.is_valid():
            from core_logic.use_cases.add_event_participants import (
                AddEventParticipantsRequest,
            )

            result = container.add_event_participants_use_case().execute(
                AddEventParticipantsRequest(
                    event_id=str(event_id),
                    student_ids=_selected_student_ids(form.cleaned_data),
                )
            )

            if result.created_count > 0:
                messages.success(request, f'✅ Добавлено {result.created_count} учеников')
            else:
                messages.info(request, 'Все выбранные ученики уже добавлены')

            return _next_or_event_detail(request, event)

    else:
        form = StudentSelectionForm()

    return render(request, 'events/add_participants.html', {
        'event': event,
        'form': form,
        'current_participants': selection_data.current_participants,
    })


def assign_variants(request, event_id):
    """Назначение вариантов участникам"""
    from infrastructure.container import container

    assignment_data = container.get_event_variant_assignment_use_case().execute(
        str(event_id),
    )
    if assignment_data.status == 'not_found':
        raise Http404("Событие не найдено")
    event = assignment_data.event

    if request.method == 'POST':
        form = VariantAssignmentForm(assignment_data, request.POST)
        if form.is_valid():
            from core_logic.use_cases.assign_event_variants import (
                AssignEventVariantsRequest,
            )

            assignments = {}
            for field_name, variant_id in form.cleaned_data.items():
                if not field_name.startswith('variant_') or not variant_id:
                    continue
                assignments[field_name.removeprefix('variant_')] = variant_id

            container.assign_event_variants_use_case().execute(
                AssignEventVariantsRequest(
                    event_id=str(event_id),
                    assignments=assignments,
                )
            )
            messages.success(request, 'Варианты успешно назначены')
            return redirect('events:detail', pk=event_id)
    else:
        form = VariantAssignmentForm(assignment_data)

    return render(request, 'events/assign_variants.html', {
        'event': event,
        'form': form
    })


def review_works(request):
    """Backward-compatible entry point for the current review dashboard."""
    return redirect('review:dashboard')


def grade_participation(request, participation_id):
    """Legacy grading endpoint kept for old links."""
    from infrastructure.container import container

    participation_data = container.get_event_participation_ref_use_case().execute(
        str(participation_id),
    )
    if participation_data.status == 'not_found':
        raise Http404("Участие не найдено")
    participation = participation_data.participation

    if request.method == 'POST':
        form = MarkForm(request.POST, request.FILES)
        if form.is_valid():
            from core_logic.use_cases.grade_student_work import GradeStudentWorkRequest

            data = form.cleaned_data
            container.grade_student_work_use_case().execute(
                GradeStudentWorkRequest(
                    participation_id=str(participation.pk),
                    score=data.get('score'),
                    points=data.get('points'),
                    max_points=data.get('max_points'),
                    teacher_comment=data.get('teacher_comment', ''),
                    mistakes_analysis=data.get('mistakes_analysis', ''),
                    recommendations=data.get('recommendations', ''),
                    checked_by_display_name=(
                        request.user.get_full_name()
                        if hasattr(request.user, 'get_full_name')
                        else ''
                    ),
                    checked_by_username=getattr(request.user, 'username', ''),
                    work_scan=data.get('work_scan'),
                    is_retake=data.get('is_retake', False),
                    is_excellent=data.get('is_excellent', False),
                    needs_attention=data.get('needs_attention', False),
                    sync_event_status=False,
                )
            )

            messages.success(request, 'Работа успешно оценена')
            return redirect('review:dashboard')
    else:
        return redirect('review:participation-review', pk=participation.pk)

from django.views.decorators.http import require_POST

@require_POST
def assign_single_variant(request, event_id):
    """Inline-назначение варианта одному участнику"""
    from core_logic.use_cases.prepare_event_action_submission import (
        PrepareEventActionSubmissionRequest,
    )
    from infrastructure.container import container

    assign_request = container.prepare_assign_single_variant_submission_use_case().execute(
        PrepareEventActionSubmissionRequest(
            event_id=str(event_id),
            data=_post_lists(request.POST),
        )
    )

    result = container.assign_single_event_variant_use_case().execute(
        assign_request,
    )

    if result.success:
        assignment = result.assignment
        messages.success(
            request,
            f'Вариант {assignment.variant_number} → {assignment.student_name}'
        )
    elif result.error == 'not_found':
        raise Http404("Событие не найдено")
    else:
        messages.error(request, 'Не указан вариант или участник')

    return _next_or_event_detail(request, event_id)


@require_POST
def change_status(request, event_id):
    """Смена статуса события"""
    from core_logic.use_cases.prepare_event_action_submission import (
        PrepareEventActionSubmissionRequest,
    )
    from infrastructure.container import container

    status_request = container.prepare_change_event_status_submission_use_case().execute(
        PrepareEventActionSubmissionRequest(
            event_id=str(event_id),
            data=_post_lists(request.POST),
        )
    )

    result = container.change_event_status_use_case().execute(
        status_request,
    )

    if result.success:
        messages.success(request, f'Статус изменён: {result.new_status_label}')
    elif not result.current_status:
        raise Http404("Событие не найдено")
    else:
        messages.error(
            request,
            f'Недопустимый переход: {result.current_status} → {result.new_status}'
        )

    return redirect('events:detail', pk=event_id)
