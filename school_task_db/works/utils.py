"""Утилиты для расчёта баллов в генераторах"""


def calc_display_points(prepared_tasks, scale):
    """Рассчитывает display_points для каждого задания.

    Если max_points заморожен — использует его.
    Иначе — считает пропорционально весам.
    Сумма display_points всегда равна scale.
    """
    if not prepared_tasks:
        return

    # Если все заморожены — просто копируем
    all_frozen = all(t.get('max_points') is not None for t in prepared_tasks)
    if all_frozen:
        for t in prepared_tasks:
            t['display_points'] = t['max_points']
        return

    # Считаем пропорционально весам
    total_weight = sum(t.get('weight', 1) for t in prepared_tasks)
    if total_weight <= 0:
        for t in prepared_tasks:
            t['display_points'] = 0
        return

    raw = [t.get('weight', 1) / total_weight * scale for t in prepared_tasks]
    floors = [int(p) for p in raw]
    remainder = int(scale - sum(floors))

    fracs = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    for i in range(remainder):
        floors[fracs[i]] += 1

    for i, t in enumerate(prepared_tasks):
        t['display_points'] = t.get('max_points') or floors[i]
