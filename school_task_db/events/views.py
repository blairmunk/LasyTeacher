from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Event, Mark
from .forms import EventForm, StudentVariantAssignmentForm

class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    paginate_by = 20

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['marks'] = Mark.objects.filter(event=self.object).select_related('student', 'variant')
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

def assign_variants(request, event_id):
    """Назначение вариантов ученикам для события"""
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = StudentVariantAssignmentForm(event, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Варианты успешно назначены!')
            return redirect('events:detail', pk=event.pk)
    else:
        form = StudentVariantAssignmentForm(event)
    
    return render(request, 'events/assign_variants.html', {
        'event': event,
        'form': form
    })
