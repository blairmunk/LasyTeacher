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
        context.update(
            container.curriculum_form_adapter.topic_list_context(
                data,
                page_number=self.request.GET.get('page'),
                paginate_by=self.paginate_by,
            )
        )
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
        context.update(container.curriculum_form_adapter.topic_detail_context(detail))
        return context


class CourseListView(TemplateView):
    template_name = 'curriculum/course_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = container.get_course_list_use_case().execute(
            year=getattr(self.request, 'current_year', None),
        )
        context.update(container.curriculum_form_adapter.course_list_context(data))
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
        context.update(container.curriculum_form_adapter.course_detail_context(detail))

        return context


def topic_subtopics_api(request, topic_id):
    """API для получения подтем определенной темы"""
    data = container.get_topic_subtopics_use_case().execute(
        TopicSubtopicsRequest(topic_id=topic_id),
    )
    return JsonResponse(container.curriculum_form_adapter.topic_subtopics_payload(data))
