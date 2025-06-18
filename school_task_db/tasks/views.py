from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q

from .models import Task, TaskImage
from .forms import TaskForm, TaskImageFormSet

class TaskListView(ListView):
    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Task.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(text__icontains=search) |
                Q(topic__icontains=search) |
                Q(section__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Импорт внутри метода для избежания циклических импортов
        from task_groups.models import AnalogGroup
        context['all_groups'] = AnalogGroup.objects.all()
        return context

class TaskDetailView(DetailView):
    model = Task
    template_name = 'tasks/detail.html'
    context_object_name = 'task'

class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = TaskImageFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            response = super().form_valid(form)
            image_formset.instance = self.object
            image_formset.save()
            messages.success(self.request, 'Задание успешно создано!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from task_groups.models import AnalogGroup 
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['image_formset'] = TaskImageFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            response = super().form_valid(form)
            image_formset.save()
            messages.success(self.request, 'Задание успешно обновлено!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

def quick_add_to_group(request):
    """Быстрое добавление задания в группу через AJAX"""
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        group_id = request.POST.get('group_id')
        action = request.POST.get('action')  # 'add' или 'remove'
        
        task = get_object_or_404(Task, pk=task_id)
        
        # Импорт внутри функции для избежания циклических импортов
        from task_groups.models import AnalogGroup
        group = get_object_or_404(AnalogGroup, pk=group_id)
        
        if action == 'add':
            # Создаем связь через промежуточную модель
            from groups.models import TaskGroup
            TaskGroup.objects.get_or_create(task=task, group=group)
            message = f'Задание добавлено в группу "{group.name}"'
        elif action == 'remove':
            from groups.models import TaskGroup
            TaskGroup.objects.filter(task=task, group=group).delete()
            message = f'Задание удалено из группы "{group.name}"'
        
        messages.success(request, message)
        return redirect('tasks:list')
    
    return redirect('tasks:list')
