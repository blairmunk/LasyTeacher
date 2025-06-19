from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db import transaction
from .models import Event, EventParticipation, Mark
from .forms import EventForm, StudentSelectionForm, MarkForm, VariantAssignmentForm

class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    paginate_by = 20
    ordering = ['-planned_date']

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['participations'] = EventParticipation.objects.filter(
            event=self.object
        ).select_related('student', 'variant').prefetch_related('mark')
        return context

class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Событие успешно создано!')
        return super().form_valid(form)

class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Событие успешно обновлено!')
        return super().form_valid(form)

def add_participants(request, event_id):
    """Добавление участников в событие"""
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = StudentSelectionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Получаем выбранных учеников
                students = []
                
                if form.cleaned_data['student_group']:
                    students.extend(form.cleaned_data['student_group'].students.all())
                
                if form.cleaned_data['individual_students']:
                    students.extend(form.cleaned_data['individual_students'])
                
                # Создаем участие для каждого ученика
                created_count = 0
                for student in students:
                    participation, created = EventParticipation.objects.get_or_create(
                        event=event,
                        student=student,
                        defaults={'status': 'assigned'}
                    )
                    if created:
                        created_count += 1
                
                messages.success(request, f'Добавлено {created_count} участников')
                return redirect('events:detail', pk=event.pk)
    else:
        form = StudentSelectionForm()
    
    return render(request, 'events/add_participants.html', {
        'event': event,
        'form': form
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
    # Получаем все события, требующие проверки
    events_to_review = Event.objects.filter(
        status__in=['completed', 'reviewing']
    ).select_related('work', 'course')
    
    # Получаем участия, требующие проверки
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
    
    # Получаем или создаем отметку
    mark, created = Mark.objects.get_or_create(participation=participation)
    
    if request.method == 'POST':
        form = MarkForm(request.POST, request.FILES, instance=mark)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.checked_by = request.user.get_full_name() or request.user.username
            mark.save()
            
            # Обновляем статус участия
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
