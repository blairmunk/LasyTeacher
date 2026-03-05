from django.shortcuts import render
from django.views.generic import TemplateView
from .utils import search_by_uuid


class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            from tasks.models import Task
            context['tasks_count'] = Task.objects.count()
        except ImportError:
            context['tasks_count'] = 0

        try:
            from works.models import Work, Variant
            context['works_count'] = Work.objects.count()
            context['variants_count'] = Variant.objects.count()
            context['orphan_variants_count'] = Variant.objects.filter(work__isnull=True).count()
        except ImportError:
            context['works_count'] = 0
            context['variants_count'] = 0
            context['orphan_variants_count'] = 0

        try:
            from students.models import Student
            context['students_count'] = Student.objects.count()
        except ImportError:
            context['students_count'] = 0

        try:
            from events.models import Event
            context['events_count'] = Event.objects.count()
        except ImportError:
            context['events_count'] = 0

        try:
            from task_groups.models import AnalogGroup
            context['groups_count'] = AnalogGroup.objects.count()
        except ImportError:
            context['groups_count'] = 0

        return context


def global_search(request):
    """Глобальный поиск по UUID и тексту"""
    from tasks.models import Task
    from works.models import Work, Variant
    from task_groups.models import AnalogGroup
    from django.db.models import Q, Count

    query = request.GET.get('q', '').strip()
    results = {}
    total_found = 0

    if query:
        clean = query.replace('#', '').strip()

        # UUID-поиск (3+ символов)
        if len(clean) >= 3:
            results['tasks'] = search_by_uuid(Task, clean)
            results['works'] = search_by_uuid(Work, clean)
            results['variants'] = search_by_uuid(Variant, clean)
            results['groups'] = search_by_uuid(AnalogGroup, clean)

        # Текстовый поиск — если UUID не дал результатов
        if not any(qs.exists() for qs in results.values() if hasattr(qs, 'exists')):
            results['tasks'] = Task.objects.filter(
                Q(text__icontains=query) | Q(answer__icontains=query)
            )[:20]
            results['works'] = Work.objects.filter(
                Q(name__icontains=query)
            )[:20]
            results['variants'] = Variant.objects.filter(
                Q(work_name_snapshot__icontains=query)
            )[:20]
            results['groups'] = AnalogGroup.objects.annotate(
                task_count=Count('taskgroup')
            ).filter(
                Q(name__icontains=query)
            )[:20]

        total_found = sum(
            qs.count() if hasattr(qs, 'count') else 0
            for qs in results.values()
        )

    return render(request, 'core/search_results.html', {
        'query': query,
        'results': results,
        'total_found': total_found,
    })
