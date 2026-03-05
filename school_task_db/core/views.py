from django.shortcuts import render
from django.views.generic import TemplateView
from .utils import search_by_uuid, pluralize_results


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
            context['orphan_variants_count'] = Variant.objects.filter(
                work__isnull=True
            ).count()
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
    """Глобальный поиск: UUID + текст"""
    from tasks.models import Task
    from works.models import Work, Variant
    from task_groups.models import AnalogGroup
    from django.db.models import Q

    raw_query = request.GET.get('q', '').strip()

    # Чистим кавычки и скобки
    query = raw_query.replace('"', '').replace("'", '').replace('«', '').replace('»', '')
    query = query.replace('(', ' ').replace(')', ' ').strip()

    results = {}
    total_found = 0
    search_mode = None

    if not query:
        return render(request, 'core/search_results.html', {
            'query': raw_query, 'results': {}, 'total_found': 0,
            'search_mode': None, 'found_text': '',
        })

    # Определяем: hex-like запрос (UUID) или текстовый
    hex_clean = query.replace('#', '').replace('-', '').replace(' ', '').lower()
    is_hex = len(hex_clean) >= 3 and all(
        c in '0123456789abcdef' for c in hex_clean
    )

    # === UUID-поиск ===
    if is_hex:
        search_mode = 'uuid'
        results = {
            'tasks': search_by_uuid(Task, hex_clean, related_uuid_fields=['topic', 'subtopic']),
            'works': search_by_uuid(Work, hex_clean),
            'variants': search_by_uuid(Variant, hex_clean, related_uuid_fields=['work']),
            'groups': search_by_uuid(AnalogGroup, hex_clean),
        }
        total_found = sum(qs.count() for qs in results.values())

    # === Текстовый поиск (если не hex, или UUID ничего не нашёл) ===
    if not is_hex or total_found == 0:
        if total_found == 0 and is_hex:
            search_mode = 'uuid+text'
        else:
            search_mode = 'text'

        # Разбиваем на слова (минимум 2 символа)
        words = [w for w in query.split() if len(w) >= 2]
        if not words and len(query) >= 2:
            words = [query]

        if words:
            # --- Задания: AND по всем словам ---
            task_q = Q()
            for word in words:
                word_q = (
                    Q(text__icontains=word) |
                    Q(answer__icontains=word)
                )
                # Пробуем topic/subtopic
                try:
                    word_q |= Q(topic__name__icontains=word)
                except Exception:
                    pass
                try:
                    word_q |= Q(subtopic__name__icontains=word)
                except Exception:
                    pass
                task_q &= word_q  # AND: каждое слово должно быть
            try:
                results['tasks'] = Task.objects.filter(task_q).distinct().select_related(
                    'topic', 'subtopic'
                )[:30]
            except Exception:
                # Фолбэк без topic/subtopic
                task_q_fb = Q()
                for word in words:
                    task_q_fb &= (Q(text__icontains=word) | Q(answer__icontains=word))
                results['tasks'] = Task.objects.filter(task_q_fb).distinct()[:30]

            # --- Работы: AND ---
            work_q = Q()
            for word in words:
                work_q &= Q(name__icontains=word)
            results['works'] = Work.objects.filter(work_q)[:20]

            # --- Варианты: AND + поиск по номеру ---
            variant_q = Q()
            number_search = None
            text_words = []
            for word in words:
                if word.isdigit():
                    number_search = int(word)
                else:
                    text_words.append(word)

            if text_words:
                for word in text_words:
                    variant_q &= Q(work_name_snapshot__icontains=word)
                if number_search:
                    variant_q &= Q(number=number_search)
                results['variants'] = Variant.objects.filter(variant_q)[:20]
            elif number_search:
                results['variants'] = Variant.objects.filter(number=number_search)[:20]
            else:
                results['variants'] = Variant.objects.none()

            # --- Группы: AND ---
            group_q = Q()
            for word in words:
                group_q &= Q(name__icontains=word)
            results['groups'] = AnalogGroup.objects.filter(group_q)[:20]

            total_found = sum(qs.count() for qs in results.values())

    return render(request, 'core/search_results.html', {
        'query': raw_query,
        'results': results,
        'total_found': total_found,
        'search_mode': search_mode,
        'found_text': pluralize_results(total_found),
    })
