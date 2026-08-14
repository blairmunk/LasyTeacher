"""Django read adapter for global application search."""

from django.db.models import Count, Q, Sum

from core_logic.entities.core import (
    GlobalSearchResults,
    SearchCourseResult,
    SearchEventResult,
    SearchGroupResult,
    SearchRelatedResult,
    SearchStudentGroupResult,
    SearchStudentResult,
    SearchSourceResult,
    SearchTaskResult,
    SearchTopicResult,
    SearchVariantResult,
    SearchWorkResult,
)
from core_logic.interfaces.global_search_repo import IGlobalSearchRepository
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from curriculum.models import Course, Topic
from events.models import Event
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup
from tasks.models import Source, Task
from works.models import Variant, Work

from .django_uuid_lookup import filter_by_uuid_suffix


class DjangoGlobalSearchRepository(IGlobalSearchRepository):
    def search_by_uuid(self, query: str):
        return GlobalSearchResults(
            tasks=self._task_results(self._search_model_by_uuid(Task, query)),
            works=self._work_results(self._search_model_by_uuid(Work, query)),
            variants=self._variant_results(
                self._search_model_by_uuid(Variant, query),
            ),
            groups=self._group_results(
                self._search_model_by_uuid(AnalogGroup, query),
            ),
            students=self._student_results(
                self._search_model_by_uuid(Student, query),
            ),
            student_groups=self._student_group_results(
                self._search_model_by_uuid(StudentGroup, query),
            ),
            events=self._event_results(
                self._search_model_by_uuid(Event, query),
            ),
            topics=self._topic_results(
                self._search_model_by_uuid(Topic, query),
            ),
            courses=self._course_results(
                self._search_model_by_uuid(Course, query),
            ),
            sources=self._source_results(
                self._search_model_by_uuid(Source, query),
            ),
        )

    def search_by_text(self, words):
        return GlobalSearchResults(
            tasks=self._task_results(self._search_tasks_by_text(words)),
            works=self._work_results(self._search_works_by_text(words)),
            variants=self._variant_results(self._search_variants_by_text(words)),
            groups=self._group_results(self._search_groups_by_text(words)),
            students=self._student_results(self._search_students_by_text(words)),
            student_groups=self._student_group_results(
                self._search_student_groups_by_text(words),
            ),
            events=self._event_results(self._search_events_by_text(words)),
            topics=self._topic_results(self._search_topics_by_text(words)),
            courses=self._course_results(self._search_courses_by_text(words)),
            sources=self._source_results(self._search_sources_by_text(words)),
        )

    @staticmethod
    def _search_model_by_uuid(model_class, query):
        return filter_by_uuid_suffix(model_class, query)

    @staticmethod
    def _search_tasks_by_text(words):
        task_q = Q()
        for word in words:
            word_q = (
                Q(text__icontains=word)
                | Q(answer__icontains=word)
                | Q(topic__name__icontains=word)
                | Q(subtopic__name__icontains=word)
            )
            task_q &= word_q

        return Task.objects.filter(task_q).distinct().select_related(
            'topic',
            'subtopic',
        )[:30]

    @staticmethod
    def _search_works_by_text(words):
        work_q = Q()
        for word in words:
            work_q &= Q(name__icontains=word)
        return Work.objects.filter(work_q)[:20]

    @staticmethod
    def _search_variants_by_text(words):
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
            return Variant.objects.filter(variant_q).select_related(
                'work',
                'assigned_student',
            )[:20]
        if number_search:
            return Variant.objects.filter(
                number=number_search,
            ).select_related(
                'work',
                'assigned_student',
            )[:20]
        return Variant.objects.none()

    @staticmethod
    def _search_groups_by_text(words):
        group_q = Q()
        for word in words:
            group_q &= Q(name__icontains=word)
        return AnalogGroup.objects.filter(group_q)[:20]

    @staticmethod
    def _search_students_by_text(words):
        student_q = Q()
        for word in words:
            student_q &= (
                Q(last_name__icontains=word)
                | Q(first_name__icontains=word)
                | Q(middle_name__icontains=word)
            )
        return Student.objects.filter(student_q)[:30]

    @staticmethod
    def _search_student_groups_by_text(words):
        group_q = Q()
        for word in words:
            group_q &= (
                Q(name__icontains=word)
                | Q(academic_year__name__icontains=word)
            )
        return StudentGroup.objects.filter(group_q).select_related(
            'academic_year',
        )[:20]

    @staticmethod
    def _search_events_by_text(words):
        event_q = Q()
        for word in words:
            event_q &= (
                Q(name__icontains=word)
                | Q(description__icontains=word)
                | Q(work__name__icontains=word)
            )
        return Event.objects.filter(event_q).select_related('work').distinct()[:20]

    @staticmethod
    def _search_topics_by_text(words):
        topic_q = Q()
        for word in words:
            topic_q &= (
                Q(name__icontains=word)
                | Q(subject__icontains=word)
                | Q(section__icontains=word)
            )
        return Topic.objects.filter(topic_q)[:20]

    @staticmethod
    def _search_courses_by_text(words):
        course_q = Q()
        for word in words:
            course_q &= (
                Q(name__icontains=word)
                | Q(subject__icontains=word)
                | Q(description__icontains=word)
            )
        return Course.objects.filter(course_q)[:20]

    @staticmethod
    def _search_sources_by_text(words):
        source_q = Q()
        for word in words:
            source_q &= (
                Q(name__icontains=word)
                | Q(short_name__icontains=word)
                | Q(author__icontains=word)
                | Q(isbn__icontains=word)
            )
        return Source.objects.filter(source_q)[:20]

    @staticmethod
    def _task_results(tasks):
        return tuple(
            SearchTaskResult(
                pk=str(task.pk),
                topic=str(task.topic),
                text=task.text,
                short_uuid=task.get_short_uuid(),
            )
            for task in tasks
        )

    @staticmethod
    def _work_results(works):
        return tuple(
            SearchWorkResult(
                pk=str(work.pk),
                name=work.name,
                work_type_display=work.get_work_type_display(),
                duration=work.duration,
                short_uuid=work.get_short_uuid(),
            )
            for work in works
        )

    @staticmethod
    def _variant_results(variants):
        variants = variants.select_related(
            'work',
            'assigned_student',
            'source_participation__event',
        ).prefetch_related(
            'eventparticipation_set__event',
        ).annotate(
            task_count_value=Count('varianttask'),
            total_max_points_value=Sum('varianttask__max_points'),
        )
        return tuple(
            SearchVariantResult(
                pk=str(variant.pk),
                display_name=resolve_variant_display_name(
                    work_name=(variant.work.name if variant.work else ''),
                    work_name_snapshot=variant.work_name_snapshot,
                    variant_type=variant.variant_type,
                    assigned_student_name=(
                        variant.assigned_student.get_short_name()
                        if variant.assigned_student
                        else ''
                    ),
                ),
                number=variant.number,
                task_count=variant.task_count_value,
                total_max_points=variant.total_max_points_value or 0,
                short_uuid=variant.get_short_uuid(),
                work=(
                    SearchRelatedResult(
                        pk=str(variant.work.pk),
                        name=variant.work.name,
                    )
                    if variant.work
                    else None
                ),
                events=DjangoGlobalSearchRepository._variant_events(variant),
            )
            for variant in variants
        )

    @staticmethod
    def _group_results(groups):
        groups = groups.annotate(task_count_value=Count('taskgroup'))
        return tuple(
            SearchGroupResult(
                pk=str(group.pk),
                name=group.name,
                task_count=group.task_count_value,
                short_uuid=group.get_short_uuid(),
            )
            for group in groups
        )

    @staticmethod
    def _student_results(students):
        return tuple(
            SearchStudentResult(
                pk=str(student.pk),
                full_name=student.get_full_name(),
                short_uuid=student.get_short_uuid(),
            )
            for student in students
        )

    @staticmethod
    def _student_group_results(groups):
        groups = groups.annotate(students_count_value=Count('students'))
        return tuple(
            SearchStudentGroupResult(
                pk=str(group.pk),
                name=str(group),
                students_count=group.students_count_value,
                short_uuid=group.get_short_uuid(),
            )
            for group in groups
        )

    @staticmethod
    def _event_results(events):
        return tuple(
            SearchEventResult(
                pk=str(event.pk),
                name=event.name,
                planned_date=event.planned_date,
                status_display=event.get_status_display(),
                short_uuid=event.get_short_uuid(),
            )
            for event in events
        )

    @staticmethod
    def _topic_results(topics):
        return tuple(
            SearchTopicResult(
                pk=str(topic.pk),
                name=topic.name,
                subject=topic.subject,
                grade_level=topic.grade_level,
                short_uuid=topic.get_short_uuid(),
            )
            for topic in topics
        )

    @staticmethod
    def _course_results(courses):
        return tuple(
            SearchCourseResult(
                pk=str(course.pk),
                name=course.name,
                subject=course.subject,
                grade_level=course.grade_level,
                short_uuid=course.get_short_uuid(),
            )
            for course in courses
        )

    @staticmethod
    def _source_results(sources):
        return tuple(
            SearchSourceResult(
                pk=str(source.pk),
                name=source.name,
                short_name=source.short_name,
                source_type_display=source.get_source_type_display(),
                short_uuid=source.get_short_uuid(),
            )
            for source in sources
        )

    @staticmethod
    def _variant_events(variant):
        events_by_id = {
            str(participation.event.pk): SearchRelatedResult(
                pk=str(participation.event.pk),
                name=participation.event.name,
            )
            for participation in variant.eventparticipation_set.all()
        }
        if variant.source_participation_id:
            event = variant.source_participation.event
            events_by_id.setdefault(
                str(event.pk),
                SearchRelatedResult(pk=str(event.pk), name=event.name),
            )
        return tuple(events_by_id.values())
