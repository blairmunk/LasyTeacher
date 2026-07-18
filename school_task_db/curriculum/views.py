from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.http import Http404, JsonResponse

from core_logic.use_cases.get_topic_subtopics import TopicSubtopicsRequest
from infrastructure.container import container


class TopicListView(TemplateView):
    template_name = 'curriculum/topic_list.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = container.get_topic_list_use_case().execute()
        paginator = Paginator(data.topics, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['topics'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return context


class TopicDetailView(TemplateView):
    template_name = 'curriculum/topic_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_topic_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail.topic is None:
            raise Http404('Тема не найдена')
        context['topic'] = detail.topic
        context['subtopics'] = detail.subtopics
        return context


class CourseListView(TemplateView):
    template_name = 'curriculum/course_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = container.get_course_list_use_case().execute()
        context['courses'] = data.courses
        return context


class CourseDetailView(TemplateView):
    template_name = 'curriculum/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_course_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail.course is None:
            raise Http404('Курс не найден')
        context['course'] = detail.course
        context['assignments'] = detail.assignments
        context['total_variants'] = detail.total_variants
        context['works_by_type'] = detail.works_by_type
        context['groups_coverage'] = detail.groups_coverage

        return context


def topic_subtopics_api(request, topic_id):
    """API для получения подтем определенной темы"""
    data = container.get_topic_subtopics_use_case().execute(
        TopicSubtopicsRequest(topic_id=topic_id),
    )
    return JsonResponse({'subtopics': data.subtopics})
