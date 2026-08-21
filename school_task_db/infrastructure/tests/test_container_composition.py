"""Structural tests for the modular dependency composition root."""

from collections import defaultdict

from django.test import SimpleTestCase

from infrastructure.container import Container


class ContainerCompositionTests(SimpleTestCase):
    def test_composition_mixins_have_unique_public_members(self):
        owners = defaultdict(list)

        for mixin in Container.__bases__:
            for name in mixin.__dict__:
                if not name.startswith('_'):
                    owners[name].append(mixin.__name__)

        collisions = {
            name: mixins
            for name, mixins in owners.items()
            if len(mixins) > 1
        }
        self.assertEqual({}, collisions)
