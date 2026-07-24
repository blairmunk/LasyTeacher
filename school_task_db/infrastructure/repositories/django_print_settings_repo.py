"""Django implementation of the print settings repository."""

from typing import List, Optional

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    DocumentSectionSpec,
    PrintSettingsSpec,
    UpdatePrintSettingsParams,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from document_generator.models import DocumentTemplate


class DjangoPrintSettingsRepository(IPrintSettingsRepository):
    """Persist print settings through the current DocumentTemplate model."""

    def list_print_settings_specs(
        self,
        document_type: str = '',
    ) -> List[PrintSettingsSpec]:
        queryset = DocumentTemplate.objects.all()
        if document_type:
            queryset = queryset.filter(template_type=document_type)
        return [template.to_print_settings_spec() for template in queryset]

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
        return template.to_print_settings_spec()

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
        return template.to_print_settings_spec()

    def create_print_settings(
        self,
        params: CreatePrintSettingsParams,
    ) -> str:
        if params.is_default:
            DocumentTemplate.objects.filter(
                template_type=params.document_type,
                is_default=True,
            ).update(is_default=False)

        template = DocumentTemplate(
            name=params.name,
            description=params.description,
            template_type=params.document_type,
            sections_config=_sections_config_from_specs(params.sections),
            is_default=params.is_default,
        )
        template.full_clean()
        template.save()
        return str(template.pk)

    def update_print_settings(
        self,
        params: UpdatePrintSettingsParams,
    ) -> bool:
        template = DocumentTemplate.objects.filter(
            pk=params.print_settings_id,
        ).first()
        if template is None:
            return False

        if params.is_default:
            DocumentTemplate.objects.filter(
                template_type=params.document_type,
                is_default=True,
            ).exclude(pk=template.pk).update(is_default=False)

        template.name = params.name
        template.description = params.description
        template.template_type = params.document_type
        template.sections_config = _sections_config_from_specs(params.sections)
        template.is_default = params.is_default
        template.full_clean()
        template.save()
        return True


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
