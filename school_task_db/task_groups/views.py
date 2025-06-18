from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q

from .models import AnalogGroup, TaskGroup
from .forms import AnalogGroupForm

class AnalogGroupListView(ListView):
    model = AnalogGroup
    template_name = 'task_groups/list.html'
    context_object_name = 'analog_groups'
    paginate_by = 20

class AnalogGroupDetailView(DetailView):
    model = AnalogGroup
    template_name = 'task_groups/detail.html'
    context_object_name = 'analoggroup'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = TaskGroup.objects.filter(group=self.object).select_related('task')
        return context

class AnalogGroupCreateView(CreateView):
    model = AnalogGroup
    form_class = AnalogGroupForm
    template_name = 'task_groups/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Группа аналогов успешно создана!')
        return super().form_valid(form)

class AnalogGroupUpdateView(UpdateView):
    model = AnalogGroup
    form_class = AnalogGroupForm
    template_name = 'task_groups/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Группа аналогов успешно обновлена!')
        return super().form_valid(form)

def add_tasks_to_group(request, group_id):
    """Добавление заданий в группу аналогов"""
    group = get_object_or_404(AnalogGroup, pk=group_id)
    
    if request.method == 'POST':
        task_ids = request.POST.getlist('selected_tasks')
        if task_ids:
            from tasks.models import Task
            tasks = Task.objects.filter(id__in=task_ids)
            for task in tasks:
                TaskGroup.objects.get_or_create(task=task, group=group)
            messages.success(request, f'Добавлено {len(tasks)} заданий в группу "{group.name}"')
        return redirect('task_groups:detail', pk=group.pk)
    
    # Получаем задания, которых еще нет в этой группе
    from tasks.models import Task
    existing_task_ids = TaskGroup.objects.filter(group=group).values_list('task_id', flat=True)
    available_tasks = Task.objects.exclude(id__in=existing_task_ids).order_by('-created_at')
    
    # Поиск
    search = request.GET.get('search')
    if search:
        available_tasks = available_tasks.filter(
            Q(text__icontains=search) |
            Q(topic__icontains=search) |
            Q(section__icontains=search)
        )
    
    context = {
        'group': group,
        'available_tasks': available_tasks,
        'search': search,
    }
    return render(request, 'task_groups/add_tasks.html', context)

def remove_task_from_group(request, group_id, task_id):
    """Удаление задания из группы аналогов"""
    group = get_object_or_404(AnalogGroup, pk=group_id)
    
    if request.method == 'POST':
        TaskGroup.objects.filter(group=group, task_id=task_id).delete()
        messages.success(request, f'Задание удалено из группы "{group.name}"')
    
    return redirect('task_groups:detail', pk=group.pk)
