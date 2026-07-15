from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import Http404
from .models import Event, EventParticipation
from .forms import EventForm, StudentSelectionForm, MarkForm, VariantAssignmentForm


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


class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    ordering = ['-planned_date']

    def get_queryset(self):
        from infrastructure.container import container

        self._event_list_data = container.get_event_list_use_case().execute()
        return self._event_list_data.events

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_list = getattr(self, '_event_list_data', None)
        if event_list is None:
            from infrastructure.container import container
            event_list = container.get_event_list_use_case().execute()

        context['planned_events'] = event_list.planned_events
        context['active_events'] = event_list.active_events
        context['graded_events'] = event_list.graded_events

        return context



class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        from infrastructure.container import container

        detail = container.get_event_detail_use_case().execute(
            event_id=str(event.pk),
            status=event.status,
            has_work=event.work_id is not None,
        )
        context['participations'] = detail.participations
        context['some_variants_assigned'] = detail.some_variants_assigned
        context['all_variants_assigned'] = detail.all_variants_assigned
        context['can_review'] = detail.can_review
        context['status_color'] = detail.status_color
        context['status_steps'] = detail.status_steps
        context['available_variants'] = detail.available_variants
        context['status_transitions'] = detail.status_transitions

        return context


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Создание события'
        context['submit_text'] = 'Создать'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        event = self.object

        from core_logic.use_cases.add_event_participants import (
            AddEventParticipantsRequest,
        )
        from infrastructure.container import container

        result = container.add_event_participants_use_case().execute(
            AddEventParticipantsRequest(
                event_id=str(event.pk),
                student_ids=_selected_student_ids(form.cleaned_data),
            )
        )

        if result.created_count:
            messages.success(
                self.request,
                f'Событие создано, добавлено {result.created_count} учеников'
            )
        else:
            messages.success(self.request, 'Событие создано')

        return response

    def get_success_url(self):
        return reverse_lazy('events:detail', kwargs={'pk': self.object.pk})


class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    success_url = reverse_lazy('events:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Редактирование события'
        context['submit_text'] = 'Сохранить'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Событие успешно обновлено!')
        return super().form_valid(form)


def add_participants(request, event_id):
    """Добавление участников в событие"""
    event = get_object_or_404(Event, pk=event_id)
    from infrastructure.container import container

    selection_data = container.get_event_participant_selection_use_case().execute(
        str(event.pk),
    )

    if request.method == 'POST':
        form = StudentSelectionForm(request.POST)
        if form.is_valid():
            from core_logic.use_cases.add_event_participants import (
                AddEventParticipantsRequest,
            )

            result = container.add_event_participants_use_case().execute(
                AddEventParticipantsRequest(
                    event_id=str(event.pk),
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
    event = get_object_or_404(Event, pk=event_id)
    from infrastructure.container import container

    assignment_data = container.get_event_variant_assignment_use_case().execute(
        str(event.pk),
    )

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
                    event_id=str(event.pk),
                    assignments=assignments,
                )
            )
            messages.success(request, 'Варианты успешно назначены')
            return redirect('events:detail', pk=event.pk)
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
    participation = get_object_or_404(EventParticipation, pk=participation_id)

    if request.method == 'POST':
        form = MarkForm(request.POST, request.FILES)
        if form.is_valid():
            from core_logic.use_cases.grade_student_work import GradeStudentWorkRequest
            from infrastructure.container import container

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
    from core_logic.use_cases.assign_single_event_variant import (
        AssignSingleEventVariantRequest,
    )
    from infrastructure.container import container

    result = container.assign_single_event_variant_use_case().execute(
        AssignSingleEventVariantRequest(
            event_id=str(event_id),
            participation_id=request.POST.get('participation_id'),
            variant_id=request.POST.get('variant_id'),
        )
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
    from core_logic.use_cases.change_event_status import (
        ChangeEventStatusRequest,
    )
    from infrastructure.container import container

    result = container.change_event_status_use_case().execute(
        ChangeEventStatusRequest(
            event_id=str(event_id),
            new_status=request.POST.get('new_status', ''),
        )
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
