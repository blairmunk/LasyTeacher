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
from document_engine.models import PrintSettings


class DjangoPrintSettingsRepository(IPrintSettingsRepository):
    """Persist print settings through Django ORM."""

    def list_print_settings_specs(
        self,
        document_type: str = '',
    ) -> List[PrintSettingsSpec]:
        queryset = PrintSettings.objects.all()
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return [
            print_settings.to_print_settings_spec()
            for print_settings in queryset
        ]

    def get_default_print_settings_spec(
        self,
        document_type: str,
    ) -> Optional[PrintSettingsSpec]:
        print_settings = (
            PrintSettings.objects
            .filter(document_type=document_type, is_default=True)
            .first()
        )
        if print_settings is None:
            return None
        return print_settings.to_print_settings_spec()

    def get_print_settings_spec(
        self,
        print_settings_id: str,
        document_type: str = '',
    ) -> Optional[PrintSettingsSpec]:
        queryset = PrintSettings.objects.filter(pk=print_settings_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        print_settings = queryset.first()
        if print_settings is None:
            return None
        return print_settings.to_print_settings_spec()

    def create_print_settings(
        self,
        params: CreatePrintSettingsParams,
    ) -> str:
        if params.is_default:
            PrintSettings.objects.filter(
                document_type=params.document_type,
                is_default=True,
            ).update(is_default=False)

        print_settings = PrintSettings(
            name=params.name,
            description=params.description,
            document_type=params.document_type,
            sections_config=_sections_config_from_specs(params.sections),
            is_default=params.is_default,
            custom_css=params.presentation.custom_css,
            custom_latex_preamble=params.presentation.custom_latex_preamble,
            html_template_override=(
                params.presentation.html_template_override
            ),
            latex_template_override=(
                params.presentation.latex_template_override
            ),
        )
        print_settings.full_clean()
        print_settings.save()
        return str(print_settings.pk)

    def update_print_settings(
        self,
        params: UpdatePrintSettingsParams,
    ) -> bool:
        print_settings = PrintSettings.objects.filter(
            pk=params.print_settings_id,
        ).first()
        if print_settings is None:
            return False

        if params.is_default:
            PrintSettings.objects.filter(
                document_type=params.document_type,
                is_default=True,
            ).exclude(pk=print_settings.pk).update(is_default=False)

        print_settings.name = params.name
        print_settings.description = params.description
        print_settings.document_type = params.document_type
        print_settings.sections_config = _sections_config_from_specs(
            params.sections,
        )
        print_settings.is_default = params.is_default
        print_settings.custom_css = params.presentation.custom_css
        print_settings.custom_latex_preamble = (
            params.presentation.custom_latex_preamble
        )
        print_settings.html_template_override = (
            params.presentation.html_template_override
        )
        print_settings.latex_template_override = (
            params.presentation.latex_template_override
        )
        print_settings.full_clean()
        print_settings.save()
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
