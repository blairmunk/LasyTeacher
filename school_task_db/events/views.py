from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.http import Http404
from django.views.decorators.http import require_POST

from core_logic.use_cases.add_event_participants import (
    AddEventParticipantsRequest,
)
from core_logic.use_cases.assign_event_variants import (
    AssignEventVariantsRequest,
)
from core_logic.use_cases.prepare_event_action_submission import (
    PrepareEventActionSubmissionRequest,
)
from infrastructure.container import container
from infrastructure.forms.event_django_forms import (
    EventForm,
    MarkForm,
    StudentSelectionForm,
    VariantAssignmentForm,
)


def _post_lists(post_data):
    return {
        key: post_data.getlist(key)
        for key in post_data
    }


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
        context.update(container.event_form_adapter.event_list_context(event_list))

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

        context.update(container.event_form_adapter.event_detail_context(detail))

        return context


class EventCreateView(TemplateView):
    template_name = 'events/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            container.event_form_adapter.event_create_context(
                kwargs.get('form') or EventForm(),
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        event_result = container.create_event_use_case().execute(
            container.event_form_adapter.event_params_from_form(form),
        )

        result = container.add_event_participants_use_case().execute(
            AddEventParticipantsRequest(
                event_id=event_result.event_id,
                student_ids=(
                    container.event_form_adapter.selected_student_ids_from_form(form)
                ),
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
        form = kwargs.get('form') or EventForm(
            initial=container.event_form_adapter.event_form_initial(event),
        )
        context.update(container.event_form_adapter.event_update_context(event, form))
        return context

    def post(self, request, *args, **kwargs):
        event = self._get_event()
        form = EventForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, object=event),
            )

        result = container.update_event_use_case().execute(
            container.event_form_adapter.event_params_from_form(
                form,
                event_id=str(event.pk),
            ),
        )
        if result.status == 'not_found':
            raise Http404('Событие не найдено')

        messages.success(request, 'Событие успешно обновлено!')
        return redirect('events:list')


def add_participants(request, event_id):
    """Добавление участников в событие"""
    selection_data = container.get_event_participant_selection_use_case().execute(
        str(event_id),
    )
    if selection_data.status == 'not_found':
        raise Http404("Событие не найдено")
    event = selection_data.event

    if request.method == 'POST':
        form = StudentSelectionForm(request.POST)
        if form.is_valid():
            result = container.add_event_participants_use_case().execute(
                AddEventParticipantsRequest(
                    event_id=str(event_id),
                    student_ids=(
                        container.event_form_adapter.selected_student_ids_from_form(
                            form,
                        )
                    ),
                )
            )

            if result.created_count > 0:
                messages.success(request, f'✅ Добавлено {result.created_count} учеников')
            else:
                messages.info(request, 'Все выбранные ученики уже добавлены')

            return _next_or_event_detail(request, event)

    else:
        form = StudentSelectionForm()

    return render(
        request,
        'events/add_participants.html',
        container.event_form_adapter.participant_selection_context(
            selection_data,
            form,
        ),
    )


def assign_variants(request, event_id):
    """Назначение вариантов участникам"""
    assignment_data = container.get_event_variant_assignment_use_case().execute(
        str(event_id),
    )
    if assignment_data.status == 'not_found':
        raise Http404("Событие не найдено")
    event = assignment_data.event

    if request.method == 'POST':
        form = VariantAssignmentForm(assignment_data, request.POST)
        if form.is_valid():
            container.assign_event_variants_use_case().execute(
                AssignEventVariantsRequest(
                    event_id=str(event_id),
                    assignments=container.event_form_adapter.assignments_from_form(
                        form,
                    ),
                )
            )
            messages.success(request, 'Варианты успешно назначены')
            return redirect('events:detail', pk=event_id)
    else:
        form = VariantAssignmentForm(assignment_data)

    return render(
        request,
        'events/assign_variants.html',
        container.event_form_adapter.variant_assignment_context(
            assignment_data,
            form,
        ),
    )


def review_works(request):
    """Backward-compatible entry point for the current review dashboard."""
    return redirect('review:dashboard')


def grade_participation(request, participation_id):
    """Legacy grading endpoint kept for old links."""
    participation_data = container.get_event_participation_ref_use_case().execute(
        str(participation_id),
    )
    if participation_data.status == 'not_found':
        raise Http404("Участие не найдено")
    participation = participation_data.participation

    if request.method == 'POST':
        form = MarkForm(request.POST, request.FILES)
        if form.is_valid():
            container.grade_student_work_use_case().execute(
                container.event_form_adapter.grade_student_work_request_from_form(
                    form,
                    participation_id=str(participation.pk),
                    checked_by_display_name=(
                        request.user.get_full_name()
                        if hasattr(request.user, 'get_full_name')
                        else ''
                    ),
                    checked_by_username=getattr(request.user, 'username', ''),
                    sync_event_status=False,
                )
            )

            messages.success(request, 'Работа успешно оценена')
            return redirect('review:dashboard')
    else:
        return redirect('review:participation-review', pk=participation.pk)


@require_POST
def assign_single_variant(request, event_id):
    """Inline-назначение варианта одному участнику"""
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
