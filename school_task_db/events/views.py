from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Count
from .models import Event, EventParticipation, Mark
from .forms import EventForm, StudentSelectionForm, MarkForm, VariantAssignmentForm


class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    ordering = ['-planned_date']

    def get_queryset(self):
        return Event.objects.select_related(
            'work', 'course'
        ).annotate(
            participant_count=Count('eventparticipation')
        ).order_by('-planned_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = context['events']

        context['planned_events'] = [e for e in events if e.status in ('planned', 'in_progress')]
        context['active_events'] = [e for e in events if e.status in ('completed', 'reviewing')]
        context['graded_events'] = [e for e in events if e.status == 'graded']

        return context



class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'

    STATUS_FLOW = [
        ('planned', 'Запланировано', 'secondary'),
        ('in_progress', 'Выполняется', 'primary'),
        ('completed', 'Завершено', 'info'),
        ('reviewing', 'На проверке', 'warning'),
        ('graded', 'Проверено', 'success'),
        ('closed', 'Закрыто', 'dark'),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        participations = EventParticipation.objects.filter(
            event=event
        ).select_related(
            'student', 'variant'
        ).order_by('student__last_name', 'student__first_name')

        for p in participations:
            try:
                p.mark_obj = Mark.objects.get(participation=p)
            except Mark.DoesNotExist:
                p.mark_obj = None

        context['participations'] = participations

        # Варианты
        active_participations = participations.exclude(status='absent')
        has_participants = active_participations.exists()
        some_variants_assigned = active_participations.filter(variant__isnull=False).exists()
        all_variants_assigned = has_participants and not active_participations.filter(
            variant__isnull=True
        ).exists()

        context['some_variants_assigned'] = some_variants_assigned
        context['all_variants_assigned'] = all_variants_assigned

        # Можно ли проверять — только после завершения
        can_review = (
            has_participants
            and some_variants_assigned
            and event.status in ('completed', 'reviewing', 'graded')
        )
        context['can_review'] = can_review

        # Цвет статуса
        status_colors = dict((s[0], s[2]) for s in self.STATUS_FLOW)
        context['status_color'] = status_colors.get(event.status, 'secondary')

        # Прогресс-бар статусов
        status_steps = []
        current_found = False
        for code, label, color in self.STATUS_FLOW:
            is_current = code == event.status
            if is_current:
                current_found = True
            passed = not current_found  # все до текущего — пройдены
            step_color = color if (passed or is_current) else 'light'
            status_steps.append({
                'code': code,
                'label': label,
                'color': step_color,
                'current': is_current,
                'passed': passed,
            })
        context['status_steps'] = status_steps

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

        # Добавляем участников
        students = []
        if form.cleaned_data.get('student_group'):
            students.extend(form.cleaned_data['student_group'].students.all())
        if form.cleaned_data.get('individual_students'):
            students.extend(form.cleaned_data['individual_students'])

        created_count = 0
        with transaction.atomic():
            for student in students:
                _, created = EventParticipation.objects.get_or_create(
                    event=event, student=student,
                    defaults={'status': 'assigned'}
                )
                if created:
                    created_count += 1

        if created_count:
            messages.success(
                self.request,
                f'Событие создано, добавлено {created_count} учеников'
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

    current_participants = EventParticipation.objects.filter(
        event=event
    ).select_related('student').order_by('student__last_name')

    if request.method == 'POST':
        form = StudentSelectionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                students = []

                if form.cleaned_data['student_group']:
                    students.extend(form.cleaned_data['student_group'].students.all())

                if form.cleaned_data['individual_students']:
                    students.extend(form.cleaned_data['individual_students'])

                created_count = 0
                for student in students:
                    participation, created = EventParticipation.objects.get_or_create(
                        event=event,
                        student=student,
                        defaults={'status': 'assigned'}
                    )
                    if created:
                        created_count += 1

                if created_count > 0:
                    messages.success(request, f'✅ Добавлено {created_count} учеников')
                else:
                    messages.info(request, 'Все выбранные ученики уже добавлены')

                return redirect('events:detail', pk=event.pk)
    else:
        form = StudentSelectionForm()

    return render(request, 'events/add_participants.html', {
        'event': event,
        'form': form,
        'current_participants': current_participants,
    })


def assign_variants(request, event_id):
    """Назначение вариантов участникам"""
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        form = VariantAssignmentForm(event, request.POST)
        if form.is_valid():
            with transaction.atomic():
                participations = EventParticipation.objects.filter(event=event)

                for participation in participations:
                    field_name = f'variant_{participation.id}'
                    variant = form.cleaned_data.get(field_name)
                    if variant:
                        participation.variant = variant
                        participation.save()

                messages.success(request, 'Варианты успешно назначены')
                return redirect('events:detail', pk=event.pk)
    else:
        form = VariantAssignmentForm(event)

    return render(request, 'events/assign_variants.html', {
        'event': event,
        'form': form
    })


def review_works(request):
    """Страница проверки работ"""
    events_to_review = Event.objects.filter(
        status__in=['completed', 'reviewing']
    ).select_related('work', 'course')

    participations_to_review = EventParticipation.objects.filter(
        event__in=events_to_review,
        status='completed'
    ).select_related('student', 'event', 'variant')

    return render(request, 'events/review_works.html', {
        'events': events_to_review,
        'participations': participations_to_review
    })


def grade_participation(request, participation_id):
    """Оценивание конкретного участия"""
    participation = get_object_or_404(EventParticipation, pk=participation_id)

    mark, created = Mark.objects.get_or_create(participation=participation)

    if request.method == 'POST':
        form = MarkForm(request.POST, request.FILES, instance=mark)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.checked_by = request.user.get_full_name() or request.user.username
            mark.save()

            participation.status = 'graded'
            participation.save()

            messages.success(request, 'Работа успешно оценена')
            return redirect('events:review-works')
    else:
        form = MarkForm(instance=mark)

    return render(request, 'events/grade_participation.html', {
        'participation': participation,
        'mark': mark,
        'form': form
    })

from django.views.decorators.http import require_POST

@require_POST
def change_status(request, event_id):
    """Смена статуса события"""
    event = get_object_or_404(Event, pk=event_id)
    new_status = request.POST.get('new_status', '')

    # Разрешённые переходы
    allowed_transitions = {
        'planned': ['in_progress', 'completed'],
        'in_progress': ['completed'],
        'completed': ['reviewing', 'graded'],
        'reviewing': ['graded', 'completed'],
        'graded': ['closed', 'reviewing'],
        'closed': ['graded'],
    }

    current = event.status
    allowed = allowed_transitions.get(current, [])

    if new_status in allowed:
        event.status = new_status
        event.save()
        messages.success(request, f'Статус изменён: {event.get_status_display()}')
    else:
        messages.error(
            request,
            f'Недопустимый переход: {current} → {new_status}'
        )

    return redirect('events:detail', pk=event.pk)

