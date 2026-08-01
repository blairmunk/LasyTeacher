"""Display values derived from an immutable variant snapshot."""


def resolve_variant_display_name(
    work_name: str = '',
    work_name_snapshot: str = '',
    variant_type: str = 'regular',
    assigned_student_name: str = '',
) -> str:
    if work_name:
        return work_name
    if work_name_snapshot:
        return work_name_snapshot

    student_name = assigned_student_name or '?'
    if variant_type == 'remedial':
        return f'Работа над ошибками — {student_name}'
    if variant_type == 'individual':
        return f'Индивидуальная — {student_name}'
    return 'Вариант без работы'
