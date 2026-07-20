from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
)
from core_logic.value_objects.document_render_options import WorkDocumentRenderOptions
from curriculum.models import Topic
from infrastructure.container import Container
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
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
