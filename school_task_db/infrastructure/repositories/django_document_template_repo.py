"""Legacy Django repository for document print settings."""

from typing import List, Optional

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    DocumentTemplateSpec,
    UpdateDocumentTemplateParams,
)
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from infrastructure.repositories.django_print_settings_repo import (
    DjangoPrintSettingsRepository,
)


class DjangoDocumentTemplateRepository(
    DjangoPrintSettingsRepository,
    IDocumentTemplateRepository,
):
    """Adapt the former template-oriented repository methods."""

    def list_template_specs(
        self,
        template_type: str = '',
    ) -> List[DocumentTemplateSpec]:
        return self.list_print_settings_specs(document_type=template_type)

    def get_default_template_spec(
        self,
        template_type: str = '',
    ) -> Optional[DocumentTemplateSpec]:
        return self.get_default_print_settings_spec(document_type=template_type)

    def get_template_spec(
        self,
        template_id: str,
        template_type: str = '',
    ) -> Optional[DocumentTemplateSpec]:
        return self.get_print_settings_spec(
            print_settings_id=template_id,
            document_type=template_type,
        )

    def create_template(
        self,
        params: CreateDocumentTemplateParams,
    ) -> str:
        return self.create_print_settings(params)

    def update_template(
        self,
        params: UpdateDocumentTemplateParams,
    ) -> bool:
        return self.update_print_settings(params)
