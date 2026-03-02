from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Count, Exists, OuterRef, Subquery

from .models import AnalogGroup, TaskGroup
from .forms import AnalogGroupForm
from tasks.models import Task
from curriculum.models import Topic, SubTopic


class AnalogGroupListView(ListView):
    model = AnalogGroup
    template_name = 'task_groups/list.html'
    context_object_name = 'analog_groups'
    paginate_by = 20

    def get_queryset(self):
        queryset = AnalogGroup.objects.annotate(
            task_count=Count('taskgroup'),
        ).order_by('name')

        # Аннотируем тему первого задания для фильтрации
        first_task_topic = Subquery(
            TaskGroup.objects.filter(
                group=OuterRef('pk')
            ).select_related('task').values('task__topic')[:1]
        )
        first_task_subtopic = Subquery(
            TaskGroup.objects.filter(
                group=OuterRef('pk')
            ).select_related('task').values('task__subtopic')[:1]
        )
        queryset = queryset.annotate(
            first_topic_id=first_task_topic,
            first_subtopic_id=first_task_subtopic,
        )

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Фильтр по теме
        topic_id = self.request.GET.get('topic')
        if topic_id:
            task_ids_in_topic = Task.objects.filter(
                topic_id=topic_id
            ).values_list('pk', flat=True)
            group_ids = TaskGroup.objects.filter(
                task_id__in=task_ids_in_topic
            ).values_list('group_id', flat=True).distinct()
            queryset = queryset.filter(pk__in=group_ids)

        # Фильтр по подтеме
        subtopic_id = self.request.GET.get('subtopic')
        if subtopic_id:
            task_ids_in_sub = Task.objects.filter(
                subtopic_id=subtopic_id
            ).values_list('pk', flat=True)
            group_ids = TaskGroup.objects.filter(
                task_id__in=task_ids_in_sub
            ).values_list('group_id', flat=True).distinct()
            queryset = queryset.filter(pk__in=group_ids)

        # Фильтр по количеству заданий
        min_tasks = self.request.GET.get('min_tasks')
        if min_tasks:
            queryset = queryset.filter(task_count__gte=int(min_tasks))

        max_tasks = self.request.GET.get('max_tasks')
        if max_tasks:
            queryset = queryset.filter(task_count__lte=int(max_tasks))

        # Фильтр: пустые / непустые
        group_filter = self.request.GET.get('group_filter')
        if group_filter == 'empty':
            queryset = queryset.filter(task_count=0)
        elif group_filter == 'nonempty':
            queryset = queryset.filter(task_count__gt=0)

        # Фильтр по сложности (есть задания этой сложности)
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            task_ids = Task.objects.filter(
                difficulty=int(difficulty)
            ).values_list('pk', flat=True)
            group_ids = TaskGroup.objects.filter(
                task_id__in=task_ids
            ).values_list('group_id', flat=True).distinct()
            queryset = queryset.filter(pk__in=group_ids)

        # Сортировка
        sort = self.request.GET.get('sort', 'name')
        if sort == 'tasks_desc':
            queryset = queryset.order_by('-task_count', 'name')
        elif sort == 'tasks_asc':
            queryset = queryset.order_by('task_count', 'name')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = Topic.objects.all().order_by('section', 'name')

        topic_id = self.request.GET.get('topic')
        if topic_id:
            context['subtopics'] = SubTopic.objects.filter(
                topic_id=topic_id
            ).order_by('order', 'name')
        else:
            context['subtopics'] = SubTopic.objects.none()

        context['difficulties'] = [
            (1, 'Базовый'),
            (2, 'Повышенный'),
            (3, 'Высокий'),
        ]

        # Текущие фильтры
        context['search_query'] = self.request.GET.get('search', '')
        context['current_topic'] = self.request.GET.get('topic', '')
        context['current_subtopic'] = self.request.GET.get('subtopic', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_group_filter'] = self.request.GET.get('group_filter', '')
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['min_tasks'] = self.request.GET.get('min_tasks', '')
        context['max_tasks'] = self.request.GET.get('max_tasks', '')

        # Статистика
        context['total_groups'] = AnalogGroup.objects.count()
        context['empty_groups'] = AnalogGroup.objects.annotate(
            tc=Count('taskgroup')
        ).filter(tc=0).count()
        context['total_tasks_in_groups'] = TaskGroup.objects.count()

        return context


class AnalogGroupDetailView(DetailView):
    model = AnalogGroup
    template_name = 'task_groups/detail.html'
    context_object_name = 'analoggroup'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = TaskGroup.objects.filter(
            group=self.object
        ).select_related('task', 'task__topic', 'task__subtopic')
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
            tasks = Task.objects.filter(id__in=task_ids)
            for task in tasks:
                TaskGroup.objects.get_or_create(task=task, group=group)
            messages.success(request, f'Добавлено {len(tasks)} заданий в группу "{group.name}"')
        return redirect('task_groups:detail', pk=group.pk)

    existing_task_ids = TaskGroup.objects.filter(group=group).values_list('task_id', flat=True)
    available_tasks = Task.objects.exclude(id__in=existing_task_ids).order_by('-created_at')

    search = request.GET.get('search')
    if search:
        available_tasks = available_tasks.filter(
            Q(text__icontains=search) |
            Q(topic__name__icontains=search)
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


# === Bulk actions ===

@require_POST
def bulk_create_work_from_groups(request):
    """Создать работу из выбранных групп аналогов"""
    import json
    from works.models import Work, WorkAnalogGroup

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    groups_data = body.get('groups', [])
    work_name = body.get('work_name', '').strip()
    work_type = body.get('work_type', 'test')
    auto_generate = body.get('auto_generate', False)
    variant_count = body.get('variant_count', 2)

    if not groups_data:
        return JsonResponse({'error': 'Не выбрано ни одной группы'}, status=400)
    if not work_name:
        return JsonResponse({'error': 'Название работы не указано'}, status=400)

    # Проверяем существование групп
    group_ids = [g['id'] for g in groups_data]
    existing_groups = AnalogGroup.objects.filter(pk__in=group_ids)
    if existing_groups.count() != len(group_ids):
        return JsonResponse({'error': 'Некоторые группы не найдены'}, status=400)

    # Создаём работу
    work = Work.objects.create(
        name=work_name,
        work_type=work_type,
    )

    # Создаём спецификацию (WorkAnalogGroup)
    for i, gdata in enumerate(groups_data, 1):
        order = gdata.get('order', i)
        count = gdata.get('count', 1)
        WorkAnalogGroup.objects.create(
            work=work,
            analog_group_id=gdata['id'],
            order=order,
            count=count,
        )

    result = {
        'success': True,
        'work_id': str(work.pk),
        'redirect_url': f'/works/{work.pk}/',
        'message': f'Создана работа «{work_name}» со спецификацией из {len(groups_data)} групп',
    }

    # Автогенерация вариантов
    if auto_generate:
        try:
            variant_count = min(int(variant_count), 10)
            work.generate_variants(variant_count)
            result['message'] += f' и {variant_count} вариантами'
            result['variants_generated'] = variant_count
        except Exception as e:
            result['warning'] = f'Работа создана, но генерация вариантов не удалась: {str(e)}'

    return JsonResponse(result)


@require_POST
def bulk_delete_groups(request):
    """Удалить выбранные группы"""
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    group_ids = body.get('group_ids', [])
    if not group_ids:
        return JsonResponse({'error': 'Не выбрано ни одной группы'}, status=400)

    deleted, _ = AnalogGroup.objects.filter(pk__in=group_ids).delete()

    return JsonResponse({
        'success': True,
        'deleted': deleted,
        'message': f'Удалено {deleted} групп',
    })
