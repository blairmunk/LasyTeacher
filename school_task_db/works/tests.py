from unittest.mock import patch
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DocumentRenderResult,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
from curriculum.models import Topic
from document_generator.models import DocumentTemplate
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from students.models import Student
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class FakeDocumentRenderContainer:
    def __init__(self, use_case=None, remedial_use_case=None):
        self.use_case = use_case
        self.remedial_use_case = remedial_use_case

    def render_work_document_use_case(self):
        return self.use_case

    def render_remedial_sheet_document_use_case(self):
        return self.remedial_use_case


class FakeRenderWorkDocumentUseCase:
    def __init__(self, result):
        self.result = result
        self.request = None

    def execute(self, request):
        self.request = request
        return self.result


class FakeRenderRemedialSheetDocumentUseCase(FakeRenderWorkDocumentUseCase):
    pass


class GenerateWorkLatexCommandTests(TestCase):
    def test_command_renders_work_document_through_container(self):
        use_case = FakeRenderWorkDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_GENERATED,
                renderer_type='latex',
                file_type='latex',
                files=[
                    GeneratedDocumentFile(
                        filename='work_1.tex',
                        size_kb=1.5,
                    ),
                ],
                source_name='Контрольная',
            ),
        )
        fake_container = FakeDocumentRenderContainer(use_case)
        stdout = StringIO()

        with patch(
            'works.management.commands.generate_work_latex.container',
            fake_container,
        ):
            call_command(
                'generate_work_latex',
                'work-1',
                '--format',
                'latex',
                '--with-answers',
                stdout=stdout,
            )

        request = use_case.request
        self.assertEqual(request.work_id, 'work-1')
        self.assertEqual(request.options.renderer_type, 'latex')
        self.assertEqual(request.options.answer_type, 'with_answers')
        self.assertIn(
            'generate_work_latex is deprecated',
            stdout.getvalue(),
        )
        self.assertIn('Created latex document for Контрольная', stdout.getvalue())
        self.assertIn('work_1.tex', stdout.getvalue())

    def test_command_raises_for_missing_work(self):
        fake_container = FakeDocumentRenderContainer(
            FakeRenderWorkDocumentUseCase(
                result=DocumentRenderResult(
                    status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                    renderer_type='latex',
                ),
            )
        )

        with patch(
            'works.management.commands.generate_work_latex.container',
            fake_container,
        ):
            with self.assertRaises(CommandError):
                call_command('generate_work_latex', 'missing', '--format', 'latex')


class GeneratePdfCommandTests(TestCase):
    def test_command_renders_work_pdf_through_container(self):
        use_case = FakeRenderWorkDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_GENERATED,
                renderer_type='pdf',
                file_type='pdf',
                files=[
                    GeneratedDocumentFile(
                        filename='work_1.pdf',
                        size_kb=2.5,
                    ),
                ],
                source_name='Контрольная',
            ),
        )
        stdout = StringIO()

        with patch(
            'works.management.commands.generate_pdf.container',
            FakeDocumentRenderContainer(use_case),
        ):
            call_command(
                'generate_pdf',
                'work',
                'work-1',
                '--format',
                'A5',
                '--with-answers',
                stdout=stdout,
            )

        request = use_case.request
        self.assertEqual(request.work_id, 'work-1')
        self.assertEqual(request.options.renderer_type, 'pdf')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertEqual(request.options.answer_type, 'with_answers')
        self.assertIn('generate_pdf is deprecated', stdout.getvalue())
        self.assertIn('Created PDF document for Контрольная', stdout.getvalue())
        self.assertIn('work_1.pdf', stdout.getvalue())

    def test_command_raises_for_missing_work(self):
        fake_container = FakeDocumentRenderContainer(
            FakeRenderWorkDocumentUseCase(
                result=DocumentRenderResult(
                    status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                    renderer_type='pdf',
                ),
            )
        )

        with patch(
            'works.management.commands.generate_pdf.container',
            fake_container,
        ):
            with self.assertRaises(CommandError):
                call_command('generate_pdf', 'work', 'missing')


class RenderWorkDocumentCommandTests(TestCase):
    def test_command_renders_work_document_through_container(self):
        use_case = FakeRenderWorkDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_GENERATED,
                renderer_type='html',
                file_type='html',
                files=[
                    GeneratedDocumentFile(
                        filename='work_1.html',
                        size_kb=1.2,
                    ),
                ],
                source_name='Контрольная',
            ),
        )
        stdout = StringIO()

        with patch(
            'works.management.commands.render_work_document.container',
            FakeDocumentRenderContainer(use_case),
        ):
            call_command(
                'render_work_document',
                'work-1',
                '--renderer',
                'html',
                '--page-format',
                'A5',
                '--with-answers',
                stdout=stdout,
            )

        request = use_case.request
        self.assertEqual(request.work_id, 'work-1')
        self.assertEqual(request.options.renderer_type, 'html')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertEqual(request.options.answer_type, 'with_answers')
        self.assertIn('Created html document for Контрольная', stdout.getvalue())
        self.assertIn('work_1.html', stdout.getvalue())

    def test_command_raises_for_missing_work(self):
        fake_container = FakeDocumentRenderContainer(
            FakeRenderWorkDocumentUseCase(
                result=DocumentRenderResult(
                    status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                    renderer_type='pdf',
                ),
            )
        )

        with patch(
            'works.management.commands.render_work_document.container',
            fake_container,
        ):
            with self.assertRaises(CommandError):
                call_command('render_work_document', 'missing')


class RenderRemedialSheetDocumentCommandTests(TestCase):
    def test_command_renders_remedial_sheet_document_through_container(self):
        use_case = FakeRenderRemedialSheetDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_GENERATED,
                renderer_type='pdf',
                file_type='pdf',
                files=[
                    GeneratedDocumentFile(
                        filename='remedial_1.pdf',
                        size_kb=2.4,
                    ),
                ],
                source_name='',
            ),
        )
        stdout = StringIO()

        with patch(
            'works.management.commands.render_remedial_sheet_document.container',
            FakeDocumentRenderContainer(remedial_use_case=use_case),
        ):
            call_command(
                'render_remedial_sheet_document',
                'variant-1',
                '--renderer',
                'pdf',
                '--page-format',
                'A5',
                '--answer-type',
                'with_full_solutions',
                stdout=stdout,
            )

        request = use_case.request
        self.assertEqual(request.variant_id, 'variant-1')
        self.assertEqual(request.options.renderer_type, 'pdf')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertEqual(request.options.answer_type, 'with_full_solutions')
        self.assertIn('Created pdf document', stdout.getvalue())
        self.assertIn('remedial_1.pdf', stdout.getvalue())

    def test_command_raises_for_non_remedial_variant(self):
        use_case = FakeRenderRemedialSheetDocumentUseCase(
            result=DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
                renderer_type='pdf',
            ),
        )

        with patch(
            'works.management.commands.render_remedial_sheet_document.container',
            FakeDocumentRenderContainer(remedial_use_case=use_case),
        ):
            with self.assertRaises(CommandError):
                call_command('render_remedial_sheet_document', 'variant-1')


class WorkDetailViewTests(TestCase):
    def setUp(self):
        self.work = Work.objects.create(
            name='Контрольная',
            work_type='test',
            max_score=5,
        )
        self.topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.variant = Variant.objects.create(
            work=self.work,
            number=1,
            work_name_snapshot=self.work.name,
            max_score_snapshot=5,
        )

    def test_detail_uses_clean_context_data_without_analog_groups(self):
        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['work'].pk, str(self.work.pk))
        self.assertEqual(response.context['work'].name, self.work.name)
        self.assertEqual(len(response.context['variants']), 1)
        self.assertEqual(response.context['analog_groups'], [])
        self.assertEqual(response.context['spec_preview'], [])
        self.assertTrue(response.context['show_sync_button'])

    def test_detail_exposes_document_rendering_dom_markers(self):
        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertContains(response, 'document-rendering-block')
        self.assertContains(response, 'id="generation"')
        self.assertContains(response, 'data-rendering-block')
        self.assertContains(response, 'btn-render-doc')
        self.assertContains(response, 'data-rendering-form')
        self.assertContains(response, 'render-toast-box')
        self.assertContains(response, 'advanced-rendering-form')
        self.assertContains(response, 'data-document-template-select')
        self.assertContains(response, 'data-template-selection-notice')
        self.assertContains(response, 'data-template-controlled-options')
        self.assertContains(
            response,
            'Выбранный шаблон задаёт состав и порядок секций документа.',
        )
        self.assertContains(response, 'Состав по умолчанию')
        self.assertContains(response, 'document_style')
        self.assertContains(response, 'Рабочий лист')
        self.assertContains(response, 'Печать')
        self.assertContains(response, 'break_between_variants')

    def test_detail_exposes_work_template_selector(self):
        template = DocumentTemplate.objects.create(
            name='Кастомный шаблон работы',
            template_type=DocumentTemplate.TemplateType.WORK,
            sections_config=[{'type': 'header'}],
            custom_latex_preamble='\\usepackage{multicol}',
        )

        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertEqual(
            response.context['work_document_templates'][0].template_id,
            str(template.pk),
        )
        self.assertContains(response, 'name="template_id"')
        self.assertContains(response, 'Кастомный шаблон работы')
        self.assertContains(response, 'кастом')

    def test_remedial_work_detail_exposes_batch_rendering_dom_markers(self):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )
        template = DocumentTemplate.objects.create(
            name='Шаблон листа РнО',
            template_type=DocumentTemplate.TemplateType.REMEDIAL,
            sections_config=[{'type': 'header'}],
        )

        response = self.client.get(reverse('works:detail', args=[remedial_work.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['remedial_sheet_templates'][0].template_id,
            str(template.pk),
        )
        self.assertContains(response, 'data-remedial-batch-rendering-block')
        self.assertContains(response, 'id="remedial-batch"')
        self.assertContains(response, 'data-remedial-batch-rendering-form')
        self.assertContains(response, 'data-remedial-batch-rendering-results')
        self.assertContains(response, 'data-template-selection-notice')
        self.assertContains(response, 'Печать листов работы над ошибками')
        self.assertContains(response, 'Шаблон листа РнО')

    def test_detail_returns_404_for_missing_work(self):
        response = self.client.get(
            reverse('works:detail', args=['550e8400-e29b-41d4-a716-446655440000'])
        )

        self.assertEqual(response.status_code, 404)

    def test_list_uses_clean_context_data(self):
        response = self.client.get(reverse('works:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['works'][0].pk, str(self.work.pk))
        self.assertEqual(response.context['works'][0].name, self.work.name)
        self.assertEqual(response.context['works'][0].variant_count, 1)
        self.assertEqual(response.context['works'][0].work_type, self.work.work_type)
        self.assertEqual(response.context['filters'].q, '')
        self.assertFalse(response.context['has_active_filters'])
        self.assertContains(response, 'Контрольная работа')

    def test_list_filters_and_marks_remedial_works(self):
        Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )

        response = self.client.get(
            reverse('works:list'),
            {'work_type': 'remedial'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['works']), 1)
        self.assertEqual(response.context['works'][0].work_type, 'remedial')
        self.assertTrue(response.context['works'][0].is_remedial)
        self.assertTrue(response.context['has_active_filters'])
        self.assertContains(response, 'РнО')
        self.assertContains(response, 'value="remedial" selected')

    def test_list_can_hide_remedial_works(self):
        Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )

        response = self.client.get(
            reverse('works:list'),
            {'hide_remedial': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['filters'].hide_remedial)
        self.assertNotIn(
            'remedial',
            [work.work_type for work in response.context['works']],
        )

    def test_variant_list_uses_clean_context_data(self):
        response = self.client.get(reverse('works:variant-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['variants'][0].pk, str(self.variant.pk))
        self.assertEqual(response.context['variants'][0].number, self.variant.number)
        self.assertEqual(response.context['variants'][0].task_count, 0)
        self.assertEqual(response.context['variants'][0].display_name, self.work.name)
        self.assertEqual(response.context['variants'][0].variant_type, 'regular')

    def test_variant_list_shows_remedial_variant_entry_point(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        remedial_variant = Variant.objects.create(
            work=None,
            number=2,
            work_name_snapshot='Работа над ошибками',
            variant_type='remedial',
            assigned_student=student,
            source_work=self.work,
        )

        response = self.client.get(reverse('works:variant-list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Работа над ошибками')
        self.assertContains(response, 'Петров П.')
        self.assertContains(
            response,
            reverse('works:variant-detail', args=[remedial_variant.pk])
            + '#remedial-render',
        )
        self.assertContains(response, 'Лист ошибок')

    def test_create_view_saves_work_and_specification_formset(self):
        group = AnalogGroup.objects.create(name='Кинематика')

        response = self.client.post(
            reverse('works:create'),
            {
                'name': 'Новая работа',
                'work_type': 'test',
                'duration': '45',
                'max_score': '10',
                'workanaloggroup_set-TOTAL_FORMS': '1',
                'workanaloggroup_set-INITIAL_FORMS': '0',
                'workanaloggroup_set-MIN_NUM_FORMS': '0',
                'workanaloggroup_set-MAX_NUM_FORMS': '1000',
                'workanaloggroup_set-0-analog_group': str(group.pk),
                'workanaloggroup_set-0-count': '2',
                'workanaloggroup_set-0-order': '1',
                'workanaloggroup_set-0-weight': '3',
            },
        )

        work = Work.objects.get(name='Новая работа')
        self.assertRedirects(
            response,
            reverse('works:detail', args=[work.pk]),
            fetch_redirect_response=False,
        )
        spec = WorkAnalogGroup.objects.get(work=work)
        self.assertEqual(spec.analog_group, group)
        self.assertEqual(spec.count, 2)
        self.assertEqual(spec.order, 1)
        self.assertEqual(spec.weight, 3)

    def test_update_view_saves_work_and_specification_formset(self):
        old_group = AnalogGroup.objects.create(name='Старая группа')
        new_group = AnalogGroup.objects.create(name='Новая группа')
        spec = WorkAnalogGroup.objects.create(
            work=self.work,
            analog_group=old_group,
            count=1,
            order=1,
            weight=1,
        )

        response = self.client.post(
            reverse('works:update', args=[self.work.pk]),
            {
                'name': 'Обновлённая работа',
                'work_type': 'quiz',
                'duration': '30',
                'max_score': '12',
                'workanaloggroup_set-TOTAL_FORMS': '1',
                'workanaloggroup_set-INITIAL_FORMS': '1',
                'workanaloggroup_set-MIN_NUM_FORMS': '0',
                'workanaloggroup_set-MAX_NUM_FORMS': '1000',
                'workanaloggroup_set-0-id': str(spec.pk),
                'workanaloggroup_set-0-analog_group': str(new_group.pk),
                'workanaloggroup_set-0-count': '3',
                'workanaloggroup_set-0-order': '1',
                'workanaloggroup_set-0-weight': '4',
            },
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        self.work.refresh_from_db()
        updated_spec = WorkAnalogGroup.objects.get(work=self.work)
        self.assertEqual(self.work.name, 'Обновлённая работа')
        self.assertEqual(self.work.work_type, 'quiz')
        self.assertEqual(self.work.duration, 30)
        self.assertEqual(self.work.max_score, 12)
        self.assertEqual(updated_spec.analog_group, new_group)
        self.assertEqual(updated_spec.count, 3)
        self.assertEqual(updated_spec.weight, 4)

    def test_update_view_returns_404_for_missing_work(self):
        response = self.client.get(
            reverse(
                'works:update',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_detail_uses_clean_context_data_with_spec_preview(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        WorkAnalogGroup.objects.create(
            work=self.work,
            analog_group=group,
            count=1,
            weight=2,
            order=1,
        )
        VariantTask.objects.create(
            variant=self.variant,
            task=task,
            order=1,
            max_points=5,
            weight=2,
        )

        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['analog_groups']), 1)
        self.assertEqual(
            response.context['spec_preview'][0].wg.analog_group.pk,
            str(group.pk),
        )
        self.assertEqual(
            response.context['spec_preview'][0].wg.analog_group.name,
            group.name,
        )
        self.assertFalse(response.context['show_sync_button'])

    def test_sync_analog_groups_view_uses_clean_use_case(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        VariantTask.objects.create(
            variant=self.variant,
            task=task,
            order=1,
            max_points=5,
            weight=2,
        )

        response = self.client.post(
            reverse('works:sync-groups', args=[self.work.pk])
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        groups = WorkAnalogGroup.objects.filter(work=self.work)
        self.assertEqual(groups.count(), 1)
        self.assertEqual(groups[0].analog_group, group)

    def test_sync_analog_groups_view_returns_404_for_missing_work(self):
        response = self.client.post(
            reverse(
                'works:sync-groups',
                args=['00000000-0000-0000-0000-000000000000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_compose_variants_view_uses_clean_use_case(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        WorkAnalogGroup.objects.create(
            work=self.work,
            analog_group=group,
            count=1,
            weight=2,
            order=1,
        )
        Variant.objects.filter(work=self.work).delete()
        self.work.variant_counter = 0
        self.work.save()

        response = self.client.post(
            reverse('works:compose-variants', args=[self.work.pk]),
            {'count': '2'},
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        self.work.refresh_from_db()
        variants = Variant.objects.filter(work=self.work)
        self.assertEqual(variants.count(), 2)
        self.assertEqual(self.work.variant_counter, 2)
        self.assertEqual(variants.first().varianttask_set.count(), 1)

    def test_legacy_generate_variants_route_still_composes_variants(self):
        group = AnalogGroup.objects.create(name='Кинематика')
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        WorkAnalogGroup.objects.create(
            work=self.work,
            analog_group=group,
            count=1,
            weight=2,
            order=1,
        )
        Variant.objects.filter(work=self.work).delete()
        self.work.variant_counter = 0
        self.work.save()

        response = self.client.post(
            reverse('works:generate-variants', args=[self.work.pk]),
            {'count': '1'},
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(Variant.objects.filter(work=self.work).count(), 1)

    def test_compose_variants_view_uses_clean_form_data(self):
        response = self.client.get(
            reverse('works:compose-variants', args=[self.work.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'works/compose_variants.html')
        self.assertEqual(response.context['work'].pk, str(self.work.pk))
        self.assertEqual(response.context['work'].name, self.work.name)
        self.assertEqual(response.context['work_groups'], [])
        self.assertIn('form', response.context)

    def test_legacy_generate_variants_route_returns_404_for_missing_work_on_get(self):
        response = self.client.get(
            reverse(
                'works:generate-variants',
                args=['00000000-0000-0000-0000-000000000000'],
            ),
        )

        self.assertEqual(response.status_code, 404)

    def test_legacy_generate_variants_route_returns_404_for_missing_work(self):
        response = self.client.post(
            reverse(
                'works:generate-variants',
                args=['00000000-0000-0000-0000-000000000000'],
            ),
            {'count': '2'},
        )

        self.assertEqual(response.status_code, 404)

    def test_create_work_from_orphans_view_uses_clean_use_case(self):
        first_orphan = Variant.objects.create(
            work=None,
            number=10,
            work_name_snapshot='Сирота 1',
            variant_type='individual',
        )
        second_orphan = Variant.objects.create(
            work=None,
            number=11,
            work_name_snapshot='Сирота 2',
            variant_type='regular',
        )
        task = Task.objects.create(
            text='Задание для сироты',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=4,
        )
        VariantTask.objects.create(
            variant=first_orphan,
            task=task,
            order=1,
            max_points=4,
            weight=4,
        )
        VariantTask.objects.create(
            variant=second_orphan,
            task=task,
            order=1,
            max_points=2,
            weight=2,
        )

        response = self.client.post(
            reverse('works:create-work-from-orphans'),
            {
                'variant_ids': [str(first_orphan.pk), str(second_orphan.pk)],
                'work_name': '  Индивидуальная подборка  ',
            },
        )

        work = Work.objects.get(name='Индивидуальная подборка')
        self.assertRedirects(
            response,
            reverse('works:detail', args=[work.pk]),
            fetch_redirect_response=False,
        )
        first_orphan.refresh_from_db()
        second_orphan.refresh_from_db()
        self.assertEqual(work.work_type, 'individual')
        self.assertEqual(work.max_score, 4)
        self.assertEqual(work.variant_counter, 2)
        self.assertEqual(first_orphan.work, work)
        self.assertEqual(second_orphan.work, work)
        self.assertEqual(first_orphan.number, 1)
        self.assertEqual(second_orphan.number, 2)

    def test_variant_detail_view_uses_clean_context_data(self):
        task = Task.objects.create(
            text='Задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        VariantTask.objects.create(
            variant=self.variant,
            task=task,
            order=1,
            max_points=2,
            weight=2,
        )

        response = self.client.get(
            reverse('works:variant-detail', args=[self.variant.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['variant'].pk, str(self.variant.pk))
        self.assertEqual(len(response.context['variant_tasks']), 1)
        self.assertEqual(response.context['variant_tasks'][0].task.pk, str(task.pk))
        self.assertEqual(response.context['variant_tasks'][0].task.text, task.text)
        self.assertEqual(response.context['total_max_points'], 2)

    def test_remedial_variant_detail_exposes_rendering_dom_markers(self):
        remedial_variant = Variant.objects.create(
            work=None,
            number=2,
            variant_type='remedial',
            source_work=self.work,
        )

        response = self.client.get(
            reverse('works:variant-detail', args=[remedial_variant.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-remedial-render-form')
        self.assertContains(response, 'data-remedial-render-submit')
        self.assertContains(response, 'data-remedial-render-result')
        self.assertContains(response, 'remedialGenerateForm')
        self.assertContains(response, 'btnGenerateRemedial')
        self.assertContains(response, 'Печать листа работы над ошибками')
        self.assertContains(response, 'id="remedial-render"')

    def test_variant_detail_returns_404_for_missing_variant(self):
        response = self.client.get(
            reverse(
                'works:variant-detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_orphan_variant_list_view_uses_clean_context_data(self):
        orphan = Variant.objects.create(
            work=None,
            number=10,
            work_name_snapshot='Сирота',
        )

        response = self.client.get(reverse('works:orphan-variants'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_orphans'], 1)
        self.assertEqual(response.context['variants'][0].pk, str(orphan.pk))
        self.assertEqual(response.context['variants'][0].display_name, 'Сирота')
        self.assertEqual(response.context['variants'][0].task_count, 0)

    def test_variant_delete_context_uses_clean_use_case(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            variant=self.variant,
            status='graded',
        )
        VariantTask.objects.create(
            variant=self.variant,
            task=Task.objects.create(
                text='Задание',
                answer='Ответ',
                topic=self.topic,
                task_type='computational',
                difficulty=2,
            ),
            order=1,
            max_points=2,
            weight=2,
        )

        response = self.client.get(
            reverse('works:variant-delete', args=[self.variant.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['delete_info'].short_uuid,
            self.variant.get_short_uuid(),
        )
        self.assertEqual(response.context['delete_info'].work_id, str(self.work.pk))
        self.assertEqual(response.context['task_count'], 1)
        self.assertTrue(response.context['has_grades'])
        self.assertEqual(response.context['grade_count'], 1)

    def test_variant_delete_returns_404_for_missing_variant(self):
        response = self.client.get(
            reverse(
                'works:variant-delete',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_variant_delete_view_blocks_delete_when_variant_has_participations(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            variant=self.variant,
            status='graded',
        )

        response = self.client.post(
            reverse('works:variant-delete', args=[self.variant.pk]),
            {'action': 'delete'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Variant.objects.filter(pk=self.variant.pk).exists())

    def test_variant_delete_view_detaches_variant_with_participations(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        event = Event.objects.create(
            name='КР',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            variant=self.variant,
            status='graded',
        )

        response = self.client.post(
            reverse('works:variant-delete', args=[self.variant.pk]),
            {'action': 'detach'},
        )

        self.assertRedirects(
            response,
            reverse('works:variant-list'),
            fetch_redirect_response=False,
        )
        self.variant.refresh_from_db()
        self.assertIsNone(self.variant.work)

    def test_variant_delete_view_deletes_variant_without_participations(self):
        variant_id = self.variant.pk

        response = self.client.post(
            reverse('works:variant-delete', args=[variant_id]),
            {'action': 'delete'},
        )

        self.assertRedirects(
            response,
            reverse('works:detail', args=[self.work.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(Variant.objects.filter(pk=variant_id).exists())

    def test_bulk_delete_variants_view_uses_clean_use_case(self):
        first_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
        )
        second_variant = Variant.objects.create(
            work=self.work,
            number=3,
            work_name_snapshot=self.work.name,
        )
        other_work = Work.objects.create(name='Другая работа')
        other_variant = Variant.objects.create(
            work=other_work,
            number=1,
            work_name_snapshot=other_work.name,
        )

        response = self.client.post(
            reverse('works:bulk-delete-variants', args=[self.work.pk]),
            {
                'variant_ids': [
                    str(first_variant.pk),
                    str(second_variant.pk),
                    str(other_variant.pk),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'success': True,
                'deleted': 2,
                'remaining': 1,
            },
        )
        self.assertFalse(Variant.objects.filter(pk=first_variant.pk).exists())
        self.assertFalse(Variant.objects.filter(pk=second_variant.pk).exists())
        self.assertTrue(Variant.objects.filter(pk=other_variant.pk).exists())

    def test_bulk_delete_variants_view_rejects_empty_selection(self):
        response = self.client.post(
            reverse('works:bulk-delete-variants', args=[self.work.pk]),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Не выбраны варианты'})

    def test_render_work_ajax_uses_clean_content_config(self):
        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
            return_value=GeneratedDocument(file_type='html', files=[]),
        ) as render_document:
            response = self.client.post(
                reverse('works:render_work_ajax', args=[self.work.pk]),
                {
                    'renderer_type': 'html',
                    'format': 'A5',
                    'answer_type': 'with_full_solutions',
                    'include_hints': '1',
                    'include_instructions': '1',
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            'HTML документ создан (с полными решениями + подсказки + инструкции)',
        )
        render_document.assert_called_once()
        render_plan = render_document.call_args.args[0]
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                'header',
                'task_list',
                'answers',
                'short_solutions',
                'full_solutions',
            ),
        )
        self.assertEqual(
            {
                key: render_plan.recipe.sections[1].options[key]
                for key in ('include_hints', 'include_instructions')
            },
            {
                'include_hints': True,
                'include_instructions': True,
            },
        )
        self.assertEqual(
            render_plan.recipe.sections[1].options['variant_id'],
            str(self.variant.pk),
        )

    def test_render_work_ajax_returns_404_for_missing_work(self):
        response = self.client.post(
            reverse(
                'works:render_work_ajax',
                args=['00000000-0000-0000-0000-000000000000'],
            ),
            {'renderer_type': 'html'},
        )

        self.assertEqual(response.status_code, 404)

    def test_render_work_ajax_uses_document_service(self):
        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
            return_value=GeneratedDocument(
                file_type='html',
                files=[
                    GeneratedDocumentFile(
                        filename='work.html',
                        size_kb=1.0,
                    )
                ],
            ),
        ) as render_document:
            response = self.client.post(
                reverse('works:render_work_ajax', args=[self.work.pk]),
                {'renderer_type': 'html'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(
            response.json()['files'][0]['download_url'],
            reverse('works:download_rendered_file', args=['html', 'work.html']),
        )
        render_document.assert_called_once()

    def test_download_rendered_file_uses_document_service(self):
        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.get_rendered_file',
            return_value=GeneratedFileResult(
                status='ready',
                file=GeneratedFile(
                    filename='work.html',
                    content=b'<html></html>',
                    content_type='text/html',
                ),
            ),
        ) as get_rendered_file:
            response = self.client.get(
                reverse('works:download_rendered_file', args=['html', 'work.html'])
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'<html></html>')
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="work.html"',
        )
        get_rendered_file.assert_called_once_with(
            file_type='html',
            filename='work.html',
        )

    def test_render_variant_ajax_uses_clean_placeholder(self):
        response = self.client.post(
            reverse('works:render_variant_ajax', args=[self.variant.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'success': True,
                'message': (
                    'Вариант 1 работы "Контрольная" '
                    'будет добавлен в следующей версии'
                ),
                'files': [],
            },
        )

    def test_render_variant_ajax_handles_orphan_variant(self):
        orphan = Variant.objects.create(
            work=None,
            number=7,
            work_name_snapshot='Индивидуальная подборка',
        )

        response = self.client.post(
            reverse('works:render_variant_ajax', args=[orphan.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            (
                'Вариант 7 работы "Индивидуальная подборка" '
                'будет добавлен в следующей версии'
            ),
        )

    def test_render_status_ajax_reports_ready(self):
        response = self.client.get(reverse('works:render_status_ajax'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'status': 'ready',
                'message': 'Система готова к рендерингу',
            },
        )

    def test_render_remedial_sheet_ajax_uses_clean_use_case(self):
        remedial_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
            variant_type='remedial',
        )

        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
            return_value=GeneratedDocument(
                file_type='pdf',
                files=[
                    GeneratedDocumentFile(
                        filename='remedial.pdf',
                        size_kb=2.0,
                    )
                ],
            ),
        ) as render_document:
            response = self.client.post(
                reverse(
                    'works:render-remedial-sheet',
                    args=[remedial_variant.pk],
                ),
                {'renderer_type': 'pdf'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(
            response.json()['files'],
            [
                {
                    'filename': 'remedial.pdf',
                    'url': reverse(
                        'works:download_rendered_file',
                        args=['pdf', 'remedial.pdf'],
                    ),
                }
            ],
        )
        render_document.assert_called_once()

    def test_render_remedial_sheet_ajax_rejects_regular_variant(self):
        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
        ) as render_document:
            response = self.client.post(
                reverse(
                    'works:render-remedial-sheet',
                    args=[self.variant.pk],
                ),
                {'renderer_type': 'pdf'},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'status': 'error',
                'message': 'Этот вариант не является работой над ошибками',
            },
        )
        render_document.assert_not_called()

    def test_render_remedial_sheet_ajax_rejects_unsupported_renderer(self):
        remedial_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
            variant_type='remedial',
        )

        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
        ) as render_document:
            response = self.client.post(
                reverse(
                    'works:render-remedial-sheet',
                    args=[remedial_variant.pk],
                ),
                {'renderer_type': 'docx'},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'status': 'error',
                'message': 'Неподдерживаемый тип рендера: docx',
            },
        )
        render_document.assert_not_called()

    def test_render_remedial_sheet_batch_ajax_renders_work_remedial_variants(self):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )
        first_variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
        )
        second_variant = Variant.objects.create(
            work=remedial_work,
            number=2,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
        )

        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
            return_value=GeneratedDocument(
                file_type='pdf',
                files=[
                    GeneratedDocumentFile(
                        filename=f'remedial_{remedial_work.pk}.pdf',
                        size_kb=4.5,
                    )
                ],
            ),
        ) as render_document:
            response = self.client.post(
                reverse(
                    'works:render-remedial-sheet-batch',
                    args=[remedial_work.pk],
                ),
                {'renderer_type': 'pdf'},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['total_files'], 1)
        self.assertEqual(
            [file_info['name'] for file_info in payload['files']],
            [f'remedial_{remedial_work.pk}.pdf'],
        )
        self.assertEqual(render_document.call_count, 1)

    def test_render_remedial_sheet_batch_ajax_rejects_work_without_remedial_variants(self):
        response = self.client.post(
            reverse(
                'works:render-remedial-sheet-batch',
                args=[self.work.pk],
            ),
            {'renderer_type': 'pdf'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'success': False,
                'error': 'В этой работе нет remedial-вариантов для печати.',
            },
        )

    def test_django_work_repo_builds_remedial_sheet_data(self):
        student = Student.objects.create(last_name='Петров', first_name='Пётр')
        source_work = Work.objects.create(name='Исходная работа')
        remedial_work = Work.objects.create(name='Работа над ошибками')
        original_variant = Variant.objects.create(
            work=source_work,
            number=1,
            work_name_snapshot=source_work.name,
        )
        remedial_variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            assigned_student=student,
            source_work=source_work,
        )
        group = AnalogGroup.objects.create(name='Движение')
        task = Task.objects.create(
            text='Исходное задание',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        new_task = Task.objects.create(
            text='Новое задание',
            answer='Новый ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        TaskGroup.objects.create(task=task, group=group)
        original_variant_task = VariantTask.objects.create(
            variant=original_variant,
            task=task,
            order=1,
            max_points=5,
            weight=5,
        )
        VariantTask.objects.create(
            variant=remedial_variant,
            task=new_task,
            order=1,
            max_points=2,
            weight=2,
        )
        event = Event.objects.create(
            name='КР',
            work=source_work,
            planned_date=timezone.now(),
            status='graded',
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=student,
            variant=original_variant,
            status='graded',
        )
        mark = Mark.objects.create(
            participation=participation,
            score=3,
            points=2,
            max_points=5,
            task_scores={
                str(original_variant_task.pk): {
                    'task_id': str(task.pk),
                    'points': 2,
                    'max_points': 5,
                },
            },
        )

        sheet_data = DjangoWorkRepository().get_remedial_sheet_data(
            str(remedial_variant.pk),
        )

        self.assertEqual(sheet_data.variant, remedial_variant)
        self.assertEqual(sheet_data.student.pk, str(student.pk))
        self.assertEqual(sheet_data.student.short_name, student.get_short_name())
        self.assertEqual(sheet_data.source_work, source_work)
        self.assertEqual(sheet_data.mark, mark)
        self.assertEqual(sheet_data.new_tasks.count(), 1)
        self.assertEqual(len(sheet_data.original_tasks), 1)
        original_task = sheet_data.original_tasks[0]
        self.assertEqual(original_task.task, task)
        self.assertEqual(original_task.points, 2)
        self.assertEqual(original_task.max_points, 5)
        self.assertEqual(original_task.pct, 40.0)
        self.assertEqual(original_task.status, 'partial')
        self.assertEqual(original_task.group_name, 'Движение')
