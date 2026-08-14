from types import SimpleNamespace

from django.contrib import admin
from django.test import SimpleTestCase

from events.admin import EventAdmin, MarkAdmin
from events.models import Event, Mark


class EventAdminPresentationTests(SimpleTestCase):
    def test_formats_event_progress(self):
        event_admin = EventAdmin(Event, admin.site)
        event = SimpleNamespace(
            participants_count_value=4,
            completed_count_value=3,
        )

        self.assertEqual(event_admin.get_progress(event), '75%')

    def test_formats_mark_percentage_and_missing_total(self):
        mark_admin = MarkAdmin(Mark, admin.site)

        self.assertEqual(
            mark_admin.get_percentage(
                SimpleNamespace(points=7, max_points=10),
            ),
            '70.0%',
        )
        self.assertEqual(
            mark_admin.get_percentage(
                SimpleNamespace(points=7, max_points=None),
            ),
            '—',
        )
