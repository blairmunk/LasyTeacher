"""Django read adapter for available class journals."""

from core_logic.entities.journal import JournalSelectData, JournalSelectLink
from core_logic.interfaces.journal_catalog_repo import IJournalCatalogRepository
from events.models import Event
from infrastructure.repositories.django_journal_refs import (
    course_ref,
    course_scope,
    group_ref,
    group_scope,
)


class DjangoJournalCatalogRepository(IJournalCatalogRepository):
    def get_journal_select(self, year):
        courses = course_scope(year).order_by('grade_level', 'name')
        groups = group_scope(year).order_by('name')
        available_group_ids = set(groups.values_list('pk', flat=True))

        journal_links = []
        for course in courses:
            for group in course.student_groups.filter(
                pk__in=available_group_ids,
            ):
                event_count = Event.objects.filter(
                    course=course,
                    eventparticipation__student__in=group.students.all(),
                ).distinct().count()
                journal_links.append(JournalSelectLink(
                    course=course_ref(course),
                    group=group_ref(group),
                    event_count=event_count,
                ))

        return JournalSelectData(
            journal_links=tuple(journal_links),
            groups=tuple(group_ref(group) for group in groups),
            courses=tuple(course_ref(course) for course in courses),
        )
