"""Django implementation of document template repository."""

from typing import List, Optional

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from document_generator.models import DocumentTemplate


class DjangoDocumentTemplateRepository(IDocumentTemplateRepository):
    def list_template_specs(
        self,
        template_type: str = '',
    ) -> List[DocumentTemplateSpec]:
        queryset = DocumentTemplate.objects.all()
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        return [template.to_template_spec() for template in queryset]

    def get_default_template_spec(
        self,
        template_type: str,
    ) -> Optional[DocumentTemplateSpec]:
        template = (
            DocumentTemplate.objects
            .filter(template_type=template_type, is_default=True)
            .first()
        )
        if template is None:
            return None
        return template.to_template_spec()
