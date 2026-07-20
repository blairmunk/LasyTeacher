"""Django implementation of document template repository."""

from typing import List, Optional

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    DocumentTemplateSpec,
    UpdateDocumentTemplateParams,
)
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

    def get_template_spec(
        self,
        template_id: str,
        template_type: str = '',
    ) -> Optional[DocumentTemplateSpec]:
        queryset = DocumentTemplate.objects.filter(pk=template_id)
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        template = queryset.first()
        if template is None:
            return None
        return template.to_template_spec()

    def create_template(
        self,
        params: CreateDocumentTemplateParams,
    ) -> str:
        if params.is_default:
            DocumentTemplate.objects.filter(
                template_type=params.template_type,
                is_default=True,
            ).update(is_default=False)

        template = DocumentTemplate(
            name=params.name,
            description=params.description,
            template_type=params.template_type,
            sections_config=[
                {'type': section_type}
                for section_type in params.section_types
            ],
            is_default=params.is_default,
        )
        template.full_clean()
        template.save()
        return str(template.pk)

    def update_template(
        self,
        params: UpdateDocumentTemplateParams,
    ) -> bool:
        template = DocumentTemplate.objects.filter(pk=params.template_id).first()
        if template is None:
            return False

        if params.is_default:
            DocumentTemplate.objects.filter(
                template_type=params.template_type,
                is_default=True,
            ).exclude(pk=template.pk).update(is_default=False)

        template.name = params.name
        template.description = params.description
        template.template_type = params.template_type
        template.sections_config = [
            {'type': section_type}
            for section_type in params.section_types
        ]
        template.is_default = params.is_default
        template.full_clean()
        template.save()
        return True
