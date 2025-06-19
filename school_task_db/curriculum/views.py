from django.views.generic import ListView, DetailView
from .models import Topic, Course

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
