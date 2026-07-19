from unittest import TestCase

from document_generator.mixins.task_render import TaskRenderMixin


class TaskRenderMixinTests(TestCase):
    def test_safe_process_uses_shared_formula_fallback_shape(self):
        mixin = TaskRenderMixin()

        def process(text):
            raise ValueError('broken')

        with self.assertLogs('document_generator.mixins.task_render', level='ERROR'):
            result = mixin._safe_process(process, 'bad $x$', 'task text')

        self.assertEqual(
            result,
            {
                'content': 'bad $x$',
                'errors': ['task text: broken'],
                'warnings': [],
            },
        )
