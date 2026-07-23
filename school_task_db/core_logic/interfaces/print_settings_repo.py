"""Print settings repository interface.

The persistence model is still backed by document templates, so this module
exposes a clean name over the legacy repository interface.
"""

from core_logic.interfaces.document_template_repo import (
    IPrintSettingsRepository,
)
