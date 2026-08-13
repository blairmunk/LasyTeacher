import ast
from pathlib import Path
from unittest import TestCase


CORE_LOGIC_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DEPENDENCIES = {
    'codifier',
    'curriculum',
    'django',
    'document_engine',
    'events',
    'infrastructure',
    'references',
    'reports',
    'review',
    'site_settings',
    'students',
    'task_groups',
    'tasks',
    'works',
}


class CoreLogicDependencyTests(TestCase):
    def test_production_modules_do_not_depend_on_outer_layers(self):
        violations = []

        for path in sorted(CORE_LOGIC_ROOT.rglob('*.py')):
            if 'tests' in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            for node in ast.walk(tree):
                for module in _imported_modules(node):
                    if module.split('.', 1)[0] in FORBIDDEN_DEPENDENCIES:
                        violations.append(
                            f'{path.relative_to(CORE_LOGIC_ROOT)}:'
                            f'{node.lineno}: {module}'
                        )

        self.assertEqual(
            violations,
            [],
            'core_logic imports outer layers:\n' + '\n'.join(violations),
        )


def _imported_modules(node):
    if isinstance(node, ast.ImportFrom):
        return (node.module,) if node.module else ()
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    return ()
