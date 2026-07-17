from django.test import TestCase
from django.urls import reverse

from curriculum.models import Course, CourseAssignment, Topic
from task_groups.models import AnalogGroup
from works.models import Variant, Work, WorkAnalogGroup


class CourseViewsTests(TestCase):
    def test_course_list_page_renders_courses(self):
        course = Course.objects.create(
            name='Физика 9',
            subject='Физика',
            grade_level=9,
        )

        response = self.client.get(reverse('curriculum:course-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['courses']), [course])
        self.assertContains(response, 'Физика 9')

    def test_curriculum_index_redirects_to_course_list(self):
        response = self.client.get('/curriculum/')

        self.assertRedirects(
            response,
            reverse('curriculum:course-list'),
            fetch_redirect_response=False,
        )

    def test_course_detail_uses_clean_detail_context(self):
        course = Course.objects.create(
            name='Физика 9',
            subject='Физика',
            grade_level=9,
        )
        work = Work.objects.create(
            name='Контрольная',
            work_type='test',
        )
        group = AnalogGroup.objects.create(name='Скорость')
        WorkAnalogGroup.objects.create(
            work=work,
            analog_group=group,
            order=1,
            count=2,
            weight=3,
        )
        assignment = CourseAssignment.objects.create(
            course=course,
            work=work,
            order=1,
        )
        Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
        )

        response = self.client.get(
            reverse('curriculum:course-detail', args=[course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['course'].pk, str(course.pk))
        self.assertEqual(response.context['course'].name, course.name)
        self.assertEqual(response.context['assignments'][0].order, assignment.order)
        self.assertEqual(response.context['assignments'][0].work.pk, str(work.pk))
        self.assertEqual(response.context['assignments'][0].work.name, work.name)
        self.assertEqual(response.context['assignments'][0].groups_count, 1)
        self.assertEqual(response.context['assignments'][0].tasks_per_variant, 2)
        self.assertEqual(response.context['assignments'][0].variants_count, 1)
        self.assertEqual(response.context['total_variants'], 1)
        self.assertEqual(response.context['works_by_type'], {'Контрольная работа': 1})
        self.assertEqual(response.context['groups_coverage'], {'Скорость': 1})

    def test_course_detail_returns_404_for_missing_course(self):
        response = self.client.get(
            reverse(
                'curriculum:course-detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_topic_subtopics_api_returns_subtopics(self):
        topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        subtopic = topic.subtopics.create(name='Скорость', order=1)

        response = self.client.get(
            reverse('curriculum:topic-subtopics-api', args=[topic.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'subtopics': [{
                    'id': str(subtopic.pk),
                    'name': 'Скорость',
                    'description': '',
                }],
            },
        )
