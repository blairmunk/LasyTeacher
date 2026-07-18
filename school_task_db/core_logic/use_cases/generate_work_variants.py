"""Backward-compatible imports for variant composition use cases."""

from core_logic.use_cases.compose_work_variants import (
    ComposeWorkVariantsRequest,
    ComposeWorkVariantsUseCase,
)


GenerateWorkVariantsRequest = ComposeWorkVariantsRequest
GenerateWorkVariantsUseCase = ComposeWorkVariantsUseCase
