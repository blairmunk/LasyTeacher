"""Shared formula processing helpers for document renderers."""

import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


FormulaProcessResult = Dict[str, str | List[str]]
FormulaProcessFunc = Callable[[str], FormulaProcessResult]


def process_formula_text(
    text: str,
    process: FormulaProcessFunc,
    label: str = '',
    fallback_logger: logging.Logger | None = None,
) -> FormulaProcessResult:
    if not text:
        return {'content': '', 'errors': [], 'warnings': []}

    try:
        return process(text)
    except Exception as exc:
        log = fallback_logger or logger
        log.error('Formula processing failed for %s: %s', label or 'text', exc)
        error = f'{label}: {exc}' if label else str(exc)
        return {'content': text, 'errors': [error], 'warnings': []}
