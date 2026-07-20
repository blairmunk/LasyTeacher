from django.test import SimpleTestCase

from infrastructure.services.html_to_pdf_generator import (
    HtmlToPdfGenerator as InfrastructureHtmlToPdfGenerator,
)
from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator


class HtmlToPdfGeneratorCompatibilityTests(SimpleTestCase):
    def test_legacy_import_path_reexports_infrastructure_backend(self):
        self.assertIs(HtmlToPdfGenerator, InfrastructureHtmlToPdfGenerator)
