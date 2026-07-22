"""Infrastructure helpers for Django curriculum screens."""

from django.core.paginator import Paginator


class CurriculumFormAdapter:
    def topic_list_context(self, list_data, page_number, paginate_by):
        page_obj = Paginator(list_data.topics, paginate_by).get_page(page_number)
        return {
            'topics': page_obj.object_list,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
        }

    def topic_detail_context(self, detail):
        return {
            'topic': detail.topic,
            'subtopics': detail.subtopics,
        }

    def course_list_context(self, list_data):
        return {
            'courses': list_data.courses,
        }

    def course_detail_context(self, detail):
        return {
            'course': detail.course,
            'assignments': detail.assignments,
            'total_variants': detail.total_variants,
            'works_by_type': detail.works_by_type,
            'groups_coverage': detail.groups_coverage,
        }

    def topic_subtopics_payload(self, data):
        return {
            'subtopics': data.subtopics,
        }
