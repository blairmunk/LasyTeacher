from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase
from django.utils import timezone

from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
)
from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from infrastructure.container import Container
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from students.models import Student
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class DocumentContainerIntegrationTests(TestCase):
    def test_container_renders_work_html_with_sectioned_engine(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            grade_level=9,
        )
        task = Task.objects.create(
            text='Найдите силу',
            answer='10 Н',
            short_solution='F = ma',
            topic=topic,
            task_type='computational',
            difficulty=3,
        )
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            old_output_dirs = RenderedDocumentFileStore.default_output_dirs
            RenderedDocumentFileStore.default_output_dirs = {
                'html': output_dir,
                'pdf': output_dir,
                'latex': output_dir,
            }
            self.addCleanup(
                setattr,
                RenderedDocumentFileStore,
                'default_output_dirs',
                old_output_dirs,
            )

            result = Container().render_work_document_use_case().execute(
                RenderWorkDocumentRequest(
                    work_id=str(work.pk),
                    options=WorkDocumentRenderOptions(
                        renderer_type='html',
                        answer_type='with_short_solutions',
                    ),
                )
            )

            filename = result.files[0].filename
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(filename, f'work_{work.pk}.html')
        self.assertIn('Контрольная', html)
        self.assertIn('Вариант 1', html)
        self.assertIn('Найдите силу', html)
        self.assertIn('Ответы', html)
        self.assertIn('10 Н', html)
        self.assertIn('Краткие решения', html)

    def test_container_renders_remedial_html_with_sectioned_engine(self):
        student = Student.objects.create(
            first_name='Иван',
            last_name='Петров',
        )
        source_work = Work.objects.create(
            name='Контрольная по динамике',
            duration=45,
            max_score=4,
        )
        source_variant = Variant.objects.create(
            work=source_work,
            number=1,
            work_name_snapshot=source_work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            grade_level=9,
        )
        original_task = Task.objects.create(
            text='Найдите ускорение тела',
            answer='2 м/с^2',
            short_solution='a = F / m',
            topic=topic,
            task_type='computational',
            difficulty=3,
        )
        training_task = Task.objects.create(
            text='Найдите силу по массе и ускорению',
            answer='8 Н',
            short_solution='F = ma',
            topic=topic,
            task_type='computational',
            difficulty=3,
        )
        VariantTask.objects.create(
            variant=source_variant,
            task=original_task,
            order=1,
            max_points=4,
        )
        event = Event.objects.create(
            name='Проверочная',
            work=source_work,
            planned_date=timezone.now(),
            status='graded',
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=student,
            variant=source_variant,
            status='graded',
        )
        Mark.objects.create(
            participation=participation,
            score=3,
            points=1,
            max_points=4,
            task_scores={
                str(original_task.pk): {
                    'points': 1,
                    'max_points': 4,
                },
            },
        )
        remedial_variant = Variant.objects.create(
            work=None,
            number=1,
            work_name_snapshot='Работа над ошибками',
            max_score_snapshot=4,
            duration_snapshot=45,
            variant_type='remedial',
            assigned_student=student,
            source_work=source_work,
        )
        VariantTask.objects.create(
            variant=remedial_variant,
            task=training_task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            old_output_dirs = RenderedDocumentFileStore.default_output_dirs
            RenderedDocumentFileStore.default_output_dirs = {
                'html': output_dir,
                'pdf': output_dir,
                'latex': output_dir,
            }
            self.addCleanup(
                setattr,
                RenderedDocumentFileStore,
                'default_output_dirs',
                old_output_dirs,
            )

            result = Container().render_remedial_sheet_document_use_case().execute(
                RenderRemedialSheetDocumentRequest(
                    variant_id=str(remedial_variant.pk),
                    options=RemedialSheetDocumentRenderOptions(
                        renderer_type='html',
                        answer_type='with_short_solutions',
                    ),
                )
            )

            filename = result.files[0].filename
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.source_name, 'Работа над ошибками')
        self.assertEqual(filename, f'remedial_{remedial_variant.pk}.html')
        self.assertIn('Петров Иван', html)
        self.assertIn('Исходная работа: Контрольная по динамике', html)
        self.assertIn('Часть 1. Разбор ошибок', html)
        self.assertIn('Найдите ускорение тела', html)
        self.assertIn('Частично', html)
        self.assertIn('Часть 2. Тренировочные задания', html)
        self.assertIn('Найдите силу по массе и ускорению', html)
        self.assertIn('Краткие решения', html)
        self.assertIn('F = ma', html)
