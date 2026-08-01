from unittest import TestCase

from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)


class VariantDisplayTests(TestCase):
    def test_current_work_name_has_priority_over_snapshot(self):
        self.assertEqual(
            resolve_variant_display_name(
                work_name='Новое название',
                work_name_snapshot='Старое название',
            ),
            'Новое название',
        )

    def test_snapshot_names_detached_variant(self):
        self.assertEqual(
            resolve_variant_display_name(
                work_name_snapshot='Диагностическая работа',
            ),
            'Диагностическая работа',
        )

    def test_names_personal_variant_without_snapshot(self):
        self.assertEqual(
            resolve_variant_display_name(
                variant_type='remedial',
                assigned_student_name='Иванов И.',
            ),
            'Работа над ошибками — Иванов И.',
        )

    def test_uses_fallback_for_regular_orphan(self):
        self.assertEqual(
            resolve_variant_display_name(),
            'Вариант без работы',
        )
