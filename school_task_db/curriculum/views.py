from django.views.generic import ListView, DetailView
from django.http import JsonResponse

from .models import Topic, Course
from infrastructure.container import container

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

    def get_queryset(self):
        return container.get_course_detail_use_case().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_course_detail_use_case().execute(str(self.object.pk))
        context['assignments'] = detail.assignments
        context['total_variants'] = detail.total_variants
        context['works_by_type'] = detail.works_by_type
        context['groups_coverage'] = detail.groups_coverage

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
