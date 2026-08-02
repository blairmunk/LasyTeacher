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
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from curriculum.models import Topic
from document_engine.models import PrintSettings
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from infrastructure.tests.variant_task_factory import (
    capture_attempt_snapshot,
    create_variant_task,
)
from students.models import Student
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import (
    Variant,
    Work,
    WorkAnalogGroup,
    WorkContentBlock,
)


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
                '--append-answers',
                stdout=stdout,
            )

        request = use_case.request
        self.assertEqual(request.work_id, 'work-1')
        self.assertEqual(request.options.renderer_type, 'html')
        self.assertEqual(request.options.pdf_format, 'A5')
        self.assertTrue(request.options.print_overrides.append_answers)
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
        self.assertContains(response, 'data-rendering-form')
        self.assertContains(response, 'render-toast-box')
        self.assertContains(response, 'document-rendering-form')
        self.assertContains(response, 'data-print-settings-select')
        self.assertContains(response, 'data-print-settings-selection-notice')
        self.assertContains(
            response,
            'Порядок контента берётся из спецификации работы.',
        )
        self.assertContains(response, 'Встроенное оформление')
        self.assertNotContains(response, 'btn-render-doc')
        self.assertNotContains(response, 'PDF + ответы')
        self.assertNotContains(response, 'name="document_style"')
        self.assertContains(response, 'hide_theory')
        self.assertContains(response, 'hide_text')
        self.assertContains(response, 'hide_blank_cells')
        self.assertContains(response, 'append_answers')
        self.assertContains(response, 'Печать')
        self.assertContains(response, 'break_between_variants')

    def test_detail_exposes_work_template_selector(self):
        template = PrintSettings.objects.create(
            name='Кастомный шаблон работы',
            document_type=PrintSettings.DocumentType.WORK,
            custom_latex_preamble='\\usepackage{multicol}',
            is_default=True,
        )

        response = self.client.get(reverse('works:detail', args=[self.work.pk]))

        self.assertEqual(
            response.context['work_presentation_profiles'][0].presentation_profile_id,
            str(template.pk),
        )
        self.assertContains(response, 'name="presentation_profile_id"')
        self.assertContains(response, 'Кастомный шаблон работы')
        self.assertContains(response, '(предлагается)')
        self.assertContains(
            response,
            f'value="{template.pk}"',
        )

    def test_remedial_work_detail_exposes_batch_rendering_dom_markers(self):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )
        student = Student.objects.create(
            last_name='Сидорова',
            first_name='Анна',
        )
        Variant.objects.create(
            work=remedial_work,
            number=1,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            assigned_student=student,
        )
        template = PrintSettings.objects.create(
            name='Шаблон листа РнО',
            document_type=PrintSettings.DocumentType.REMEDIAL,
            is_default=True,
        )

        response = self.client.get(reverse('works:detail', args=[remedial_work.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context[
                'remedial_sheet_presentation_profiles'
            ][0].presentation_profile_id,
            str(template.pk),
        )
        self.assertContains(response, 'data-remedial-batch-rendering-block')
        self.assertContains(response, 'id="remedial-batch"')
        self.assertContains(response, 'data-remedial-batch-rendering-form')
        self.assertContains(response, 'data-remedial-batch-rendering-results')
        self.assertContains(response, 'data-print-settings-selection-notice')
        self.assertContains(response, 'Печать листов работы над ошибками')
        self.assertContains(response, 'Создать персональные листы')
        self.assertContains(response, student.get_short_name())
        self.assertContains(response, 'Шаблон листа РнО')
        self.assertNotContains(response, 'id="generation"')
        self.assertNotContains(response, 'id="document-rendering-form"')

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
                'workanaloggroup_set-0-order': '20',
                'workanaloggroup_set-0-weight': '3',
                'content_blocks-TOTAL_FORMS': '1',
                'content_blocks-INITIAL_FORMS': '0',
                'content_blocks-MIN_NUM_FORMS': '0',
                'content_blocks-MAX_NUM_FORMS': '1000',
                'content_blocks-0-content_type': 'theory',
                'content_blocks-0-order': '10',
                'content_blocks-0-title': 'Опорная теория',
                'content_blocks-0-topics': [str(self.topic.pk)],
                'content_blocks-0-include_subtopics': 'on',
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
        self.assertEqual(spec.order, 20)
        self.assertEqual(spec.weight, 3)
        content_block = WorkContentBlock.objects.get(work=work)
        self.assertEqual(content_block.content_type, 'theory')
        self.assertEqual(content_block.order, 10)
        self.assertEqual(content_block.title, 'Опорная теория')
        self.assertEqual(list(content_block.topics.all()), [self.topic])
        self.assertTrue(content_block.include_subtopics)

    def test_update_form_exposes_existing_content_blocks(self):
        block = WorkContentBlock.objects.create(
            work=self.work,
            content_type='text',
            order=15,
            title='Инструкция',
            body='Покажите ход решения.',
        )

        response = self.client.get(
            reverse('works:update', args=[self.work.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id_content_blocks-TOTAL_FORMS')
        self.assertContains(response, 'id="content-plan-blocks"')
        self.assertContains(response, 'Теория и текст')
        self.assertContains(response, 'Покажите ход решения.')
        self.assertEqual(
            response.context['content_formset'].forms[0].instance,
            block,
        )

    def test_detail_shows_persistent_content_plan_blocks(self):
        WorkContentBlock.objects.create(
            work=self.work,
            content_type='text',
            order=15,
            title='Самопроверка',
            body='Проверьте единицы измерения.',
        )

        response = self.client.get(
            reverse('works:detail', args=[self.work.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['content_blocks'][0].content_type,
            'text',
        )
        self.assertContains(response, 'Самопроверка')
        self.assertContains(response, 'Проверьте единицы измерения.')
        self.assertContains(
            response,
            reverse('works:update', args=[self.work.pk])
            + '#content-plan-blocks',
        )

    def test_detail_exposes_content_plan_controls_when_blocks_are_empty(self):
        response = self.client.get(
            reverse('works:detail', args=[self.work.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Теоретические и текстовые блоки не заданы.',
        )
        self.assertContains(
            response,
            reverse('works:update', args=[self.work.pk])
            + '#content-plan-blocks',
        )

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
                'content_blocks-TOTAL_FORMS': '0',
                'content_blocks-INITIAL_FORMS': '0',
                'content_blocks-MIN_NUM_FORMS': '0',
                'content_blocks-MAX_NUM_FORMS': '1000',
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

    def test_update_rejects_duplicate_content_order_before_changing_work(self):
        group = AnalogGroup.objects.create(name='Динамика')

        response = self.client.post(
            reverse('works:update', args=[self.work.pk]),
            {
                'name': 'Не должно сохраниться',
                'work_type': 'quiz',
                'duration': '30',
                'max_score': '12',
                'workanaloggroup_set-TOTAL_FORMS': '1',
                'workanaloggroup_set-INITIAL_FORMS': '0',
                'workanaloggroup_set-MIN_NUM_FORMS': '0',
                'workanaloggroup_set-MAX_NUM_FORMS': '1000',
                'workanaloggroup_set-0-analog_group': str(group.pk),
                'workanaloggroup_set-0-count': '1',
                'workanaloggroup_set-0-order': '10',
                'workanaloggroup_set-0-weight': '2',
                'content_blocks-TOTAL_FORMS': '1',
                'content_blocks-INITIAL_FORMS': '0',
                'content_blocks-MIN_NUM_FORMS': '0',
                'content_blocks-MAX_NUM_FORMS': '1000',
                'content_blocks-0-content_type': 'text',
                'content_blocks-0-order': '10',
                'content_blocks-0-title': 'Инструкция',
                'content_blocks-0-body': 'Решите задачу.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Порядок блоков должен быть уникальным')
        self.work.refresh_from_db()
        self.assertEqual(self.work.name, 'Контрольная')
        self.assertEqual(self.work.work_type, 'test')
        self.assertFalse(
            WorkAnalogGroup.objects.filter(work=self.work).exists(),
        )
        self.assertFalse(
            WorkContentBlock.objects.filter(work=self.work).exists(),
        )

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
        create_variant_task(
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
        create_variant_task(
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
        create_variant_task(
            variant=first_orphan,
            task=task,
            order=1,
            max_points=4,
            weight=4,
        )
        create_variant_task(
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
        create_variant_task(
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
        student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        remedial_variant = Variant.objects.create(
            work=None,
            number=2,
            variant_type='remedial',
            source_work=self.work,
            assigned_student=student,
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
        create_variant_task(
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

    def test_render_work_ajax_uses_specification_and_print_overrides(self):
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
                    'append_answers': '1',
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            (
                'HTML документ создан '
                '(по спецификации + ответы в конце)'
            ),
        )
        render_document.assert_called_once()
        render_plan = render_document.call_args.args[0]
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                'header',
                'task_list',
                'answers',
            ),
        )
        self.assertNotIn(
            'include_hints',
            render_plan.recipe.sections[1].options,
        )
        self.assertNotIn(
            'include_instructions',
            render_plan.recipe.sections[1].options,
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

    def test_render_work_ajax_rejects_generic_print_for_remedial_work(self):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )

        with patch(
            'infrastructure.services.document_engine.'
            'DjangoDocumentEngine.render_document',
        ) as render_document:
            response = self.client.post(
                reverse('works:render_work_ajax', args=[remedial_work.pk]),
                {'renderer_type': 'pdf'},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'success': False,
                'error': (
                    'Для работы над ошибками используйте печать '
                    'персональных листов.'
                ),
            },
        )
        render_document.assert_not_called()

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
        student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        remedial_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
            variant_type='remedial',
            assigned_student=student,
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

    def test_render_remedial_sheet_ajax_rejects_unsigned_variant(self):
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
                {'renderer_type': 'pdf'},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                'status': 'error',
                'message': (
                    'Лист работы над ошибками не привязан к ученику'
                ),
            },
        )
        render_document.assert_not_called()

    def test_render_remedial_sheet_ajax_rejects_unsupported_renderer(self):
        student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        remedial_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
            variant_type='remedial',
            assigned_student=student,
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
        first_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        second_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        first_variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            assigned_student=first_student,
        )
        second_variant = Variant.objects.create(
            work=remedial_work,
            number=2,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            assigned_student=second_student,
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
                'error': (
                    'В этой работе нет персональных листов '
                    'работы над ошибками для печати.'
                ),
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
        original_variant_task = create_variant_task(
            variant=original_variant,
            task=task,
            order=1,
            max_points=5,
            weight=5,
        )
        create_variant_task(
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
        source_attempt = capture_attempt_snapshot(mark)
        remedial_variant.source_participation = participation
        remedial_variant.source_attempt_snapshot = source_attempt
        remedial_variant.save(
            update_fields=[
                'source_participation',
                'source_attempt_snapshot',
            ],
        )

        sheet_data = GetRemedialSheetDataUseCase(
            DjangoWorkRepository(),
        ).execute(str(remedial_variant.pk))

        self.assertEqual(sheet_data.variant.pk, str(remedial_variant.pk))
        self.assertEqual(sheet_data.variant.work.pk, str(remedial_work.pk))
        self.assertEqual(sheet_data.student.pk, str(student.pk))
        self.assertEqual(sheet_data.student.short_name, student.get_short_name())
        self.assertEqual(sheet_data.source_work.pk, str(source_work.pk))
        self.assertEqual(sheet_data.source_work.name, source_work.name)
        self.assertEqual(sheet_data.mark.score, mark.score)
        self.assertEqual(sheet_data.mark.points, mark.points)
        self.assertEqual(sheet_data.mark.max_points, mark.max_points)
        self.assertEqual(len(sheet_data.new_tasks), 1)
        self.assertEqual(sheet_data.new_tasks[0].task.pk, str(new_task.pk))
        self.assertEqual(len(sheet_data.original_tasks), 1)
        original_task = sheet_data.original_tasks[0]
        self.assertEqual(original_task.task.pk, str(task.pk))
        self.assertEqual(original_task.task.text, task.text)
        self.assertEqual(original_task.points, 2)
        self.assertEqual(original_task.max_points, 5)
        self.assertEqual(original_task.pct, 40.0)
        self.assertEqual(original_task.status, 'partial')
        self.assertEqual(original_task.group_name, 'Движение')
