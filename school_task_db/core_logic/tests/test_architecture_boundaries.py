"""Regression tests for the clean architecture dependency boundaries."""

import ast
from pathlib import Path
from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / 'core_logic'
PRESENTATION_PACKAGES = {
    'codifier',
    'core',
    'curriculum',
    'document_engine',
    'events',
    'references',
    'reports',
    'review',
    'site_settings',
    'students',
    'task_groups',
    'tasks',
    'works',
}


def _python_files(root):
    return sorted(
        path
        for path in root.rglob('*.py')
        if '__pycache__' not in path.parts
    )


def _imported_modules(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.lineno, node.module


def _relative_location(path, lineno):
    return f'{path.relative_to(PROJECT_ROOT)}:{lineno}'


class CleanArchitectureBoundaryTests(TestCase):
    def test_core_logic_does_not_depend_on_framework_or_application_apps(self):
        violations = []

        for path in _python_files(CORE_ROOT):
            if 'tests' in path.relative_to(CORE_ROOT).parts:
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            for lineno, module in _imported_modules(tree):
                root_package = module.split('.', 1)[0]
                if (
                    root_package in {'django', 'infrastructure'}
                    or root_package in PRESENTATION_PACKAGES
                ):
                    violations.append(
                        f'{_relative_location(path, lineno)} imports {module}'
                    )

        self.assertEqual([], violations, '\n'.join(violations))

    def test_views_do_not_import_models_or_use_orm_managers(self):
        violations = []
        view_files = sorted(PROJECT_ROOT.glob('*/views*.py'))

        for path in view_files:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            for lineno, module in _imported_modules(tree):
                if module == 'django.db.models' or module.endswith('.models'):
                    violations.append(
                        f'{_relative_location(path, lineno)} imports {module}'
                    )
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr == 'objects':
                    violations.append(
                        f'{_relative_location(path, node.lineno)} uses .objects'
                    )

        self.assertEqual([], violations, '\n'.join(violations))
