"""Pure parsing helpers for editable reference catalogs."""


def parse_simple_reference_items(items_text: str):
    return [
        line
        for raw_line in (items_text or '').splitlines()
        if (line := raw_line.strip())
    ]


def parse_subject_reference_items(items_text: str):
    items = {}
    for raw_line in (items_text or '').splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if '|' not in line:
            items[line] = line
            continue
        code, name = (part.strip() for part in line.split('|', 1))
        if code and name:
            items[code] = name
    return list(items.items())
