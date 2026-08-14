from django.test import TestCase

from infrastructure.repositories.django_uuid_lookup import (
    filter_by_uuid_suffix,
    get_unambiguous_by_uuid,
)
from works.models import Work


class DjangoUuidLookupTests(TestCase):
    def test_returns_exact_and_unambiguous_suffix_matches(self):
        work = Work.objects.create(
            id='10000000-0000-0000-0000-00000000a1b2',
            name='Первая работа',
        )

        suffix_match = get_unambiguous_by_uuid(Work, '#A1B2')
        exact_match = get_unambiguous_by_uuid(Work, str(work.pk))

        self.assertEqual(str(suffix_match.pk), str(work.pk))
        self.assertEqual(str(exact_match.pk), str(work.pk))

    def test_rejects_invalid_or_ambiguous_fragments(self):
        Work.objects.create(
            id='10000000-0000-0000-0000-00000000a1b2',
            name='Первая работа',
        )
        Work.objects.create(
            id='20000000-0000-0000-0000-00000000a1b2',
            name='Вторая работа',
        )

        self.assertIsNone(get_unambiguous_by_uuid(Work, '#A1B2'))
        self.assertIsNone(get_unambiguous_by_uuid(Work, 'не-uuid'))
        self.assertEqual(
            filter_by_uuid_suffix(Work, '#A1B2').count(),
            2,
        )
