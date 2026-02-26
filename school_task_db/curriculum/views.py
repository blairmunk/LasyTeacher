from django.views.generic import ListView, DetailView
from django.db.models import Count, Sum
from collections import Counter  # ← добавь эту строку

from .models import Topic, SubTopic, Course, CourseAssignment
from works.models import WorkAnalogGroup, Variant

class TopicListView(ListView):
    model = Topic
    template_name = 'curriculum/topic_list.html'
    context_object_name = 'topics'
    paginate_by = 20

class TopicDetailView(DetailView):
    model = Topic
    template_name = 'curriculum/topic_detail.html'
    context_object_name = 'topic'

class CourseListView(ListView):
    model = Course
    template_name = 'curriculum/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

class CourseDetailView(DetailView):
    model = Course
    template_name = 'curriculum/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        # Получаем все назначения с аннотациями
        assignments = []
        total_variants = 0
        works_by_type = Counter()
        groups_coverage = Counter()

        for ca in course.courseassignment_set.select_related('work').order_by('order'):
            work = ca.work

            # Считаем группы и задания на вариант
            work_groups = WorkAnalogGroup.objects.filter(work=work)
            groups_count = work_groups.count()
            tasks_per_variant = sum(wg.count for wg in work_groups)

            # Считаем варианты
            variants_count = Variant.objects.filter(work=work).count()
            total_variants += variants_count

            # Статистика по типам
            works_by_type[work.get_work_type_display()] += 1

            # Покрытие групп
            for wg in work_groups:
                groups_coverage[wg.analog_group.name] += 1

            # Добавляем аннотации прямо на объект
            ca.groups_count = groups_count
            ca.tasks_per_variant = tasks_per_variant
            ca.variants_count = variants_count
            assignments.append(ca)

        context['assignments'] = assignments
        context['total_variants'] = total_variants
        context['works_by_type'] = dict(works_by_type)
        context['groups_coverage'] = dict(groups_coverage.most_common())

        return context

def topic_subtopics_api(request, topic_id):
    """API для получения подтем определенной темы"""
    try:
        topic = Topic.objects.get(pk=topic_id)
        subtopics = topic.subtopics.all().order_by('order')
        data = [
            {
                'id': subtopic.id,
                'name': subtopic.name,
                'description': subtopic.description
            }
            for subtopic in subtopics
        ]
        return JsonResponse({'subtopics': data})
    except Topic.DoesNotExist:
        return JsonResponse({'subtopics': []})
