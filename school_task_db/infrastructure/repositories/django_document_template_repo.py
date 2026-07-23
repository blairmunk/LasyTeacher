"""Django implementation of document template repository."""

from typing import List, Optional

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    CreatePrintSettingsParams,
    DocumentSectionSpec,
    DocumentTemplateSpec,
    PrintSettingsSpec,
    UpdateDocumentTemplateParams,
    UpdatePrintSettingsParams,
)
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from document_generator.models import DocumentTemplate


class DjangoDocumentTemplateRepository(IDocumentTemplateRepository):
    def list_print_settings_specs(
        self,
        document_type: str = '',
    ) -> List[PrintSettingsSpec]:
        queryset = DocumentTemplate.objects.all()
        if document_type:
            queryset = queryset.filter(template_type=document_type)
        return [template.to_template_spec() for template in queryset]

    def list_template_specs(
        self,
        template_type: str = '',
    ) -> List[DocumentTemplateSpec]:
        return self.list_print_settings_specs(document_type=template_type)

    def get_default_print_settings_spec(
        self,
        document_type: str,
    ) -> Optional[PrintSettingsSpec]:
        template = (
            DocumentTemplate.objects
            .filter(template_type=document_type, is_default=True)
            .first()
        )
        if template is None:
            return None
        return template.to_template_spec()

    def get_default_template_spec(
        self,
        template_type: str = '',
    ) -> Optional[DocumentTemplateSpec]:
        return self.get_default_print_settings_spec(document_type=template_type)

    def get_print_settings_spec(
        self,
        print_settings_id: str,
        document_type: str = '',
    ) -> Optional[PrintSettingsSpec]:
        queryset = DocumentTemplate.objects.filter(pk=print_settings_id)
        if document_type:
            queryset = queryset.filter(template_type=document_type)
        template = queryset.first()
        if template is None:
            return None
        return template.to_template_spec()

    def get_template_spec(
        self,
        template_id: str,
        template_type: str = '',
    ) -> Optional[DocumentTemplateSpec]:
        return self.get_print_settings_spec(
            print_settings_id=template_id,
            document_type=template_type,
        )

    def create_print_settings(
        self,
        params: CreatePrintSettingsParams,
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
            sections_config=_sections_config_from_specs(params.sections),
            is_default=params.is_default,
        )
        template.full_clean()
        template.save()
        return str(template.pk)

    def create_template(
        self,
        params: CreateDocumentTemplateParams,
    ) -> str:
        return self.create_print_settings(params)

    def update_print_settings(
        self,
        params: UpdatePrintSettingsParams,
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
        template.sections_config = _sections_config_from_specs(params.sections)
        template.is_default = params.is_default
        template.full_clean()
        template.save()
        return True

    def update_template(
        self,
        params: UpdateDocumentTemplateParams,
    ) -> bool:
        return self.update_print_settings(params)


def _sections_config_from_specs(
    sections: tuple[DocumentSectionSpec, ...],
) -> list[dict]:
    sections_config = []
    for section in sections:
        section_config = {'type': section.section_type}
        if section.title:
            section_config['title'] = section.title
        if section.options:
            section_config['params'] = dict(section.options)
        sections_config.append(section_config)
    return sections_config
