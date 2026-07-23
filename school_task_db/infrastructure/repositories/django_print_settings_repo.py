"""Django implementation of print settings repository.

The database model is still ``DocumentTemplate``; this module exposes the
current infrastructure name for clean-architecture wiring.
"""

from infrastructure.repositories.django_document_template_repo import (
    DjangoPrintSettingsRepository,
)
