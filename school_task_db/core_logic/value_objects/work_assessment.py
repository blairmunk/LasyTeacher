"""Assessment modes supported by a work."""

WORK_ASSESSMENT_MODE_VARIANT = 'variant'
WORK_ASSESSMENT_MODE_AGGREGATE = 'aggregate'

WORK_ASSESSMENT_MODE_CHOICES = (
    (
        WORK_ASSESSMENT_MODE_VARIANT,
        'По заданиям и вариантам',
    ),
    (
        WORK_ASSESSMENT_MODE_AGGREGATE,
        'Итоговая оценка без варианта (внешний материал)',
    ),
)

WORK_ASSESSMENT_MODE_LABELS = dict(WORK_ASSESSMENT_MODE_CHOICES)
WORK_ASSESSMENT_MODES = frozenset(WORK_ASSESSMENT_MODE_LABELS)


def validate_work_assessment_mode(mode: str) -> str:
    if mode not in WORK_ASSESSMENT_MODES:
        raise ValueError(f'Unsupported work assessment mode: {mode}')
    return mode


def work_requires_variants(mode: str) -> bool:
    validate_work_assessment_mode(mode)
    return mode == WORK_ASSESSMENT_MODE_VARIANT
