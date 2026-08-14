"""Formatting and matching rules for user-facing UUID fragments."""

SHORT_UUID_LENGTH = 4
MEDIUM_UUID_LENGTH = 8
MIN_UUID_SEARCH_LENGTH = 3


def normalize_uuid_fragment(value: object) -> str:
    """Return a lowercase UUID fragment without visual separators."""
    return ''.join(
        character
        for character in str(value).strip().lower()
        if character != '-' and not character.isspace()
    ).removeprefix('#')


def is_uuid_search_fragment(value: object) -> bool:
    fragment = normalize_uuid_fragment(value)
    return (
        len(fragment) >= MIN_UUID_SEARCH_LENGTH
        and all(character in '0123456789abcdef' for character in fragment)
    )


def uuid_matches_suffix(uuid_value: object, fragment: object) -> bool:
    normalized_fragment = normalize_uuid_fragment(fragment)
    return (
        is_uuid_search_fragment(normalized_fragment)
        and normalize_uuid_fragment(uuid_value).endswith(normalized_fragment)
    )


def format_short_uuid(
    uuid_value: object,
    length: int = SHORT_UUID_LENGTH,
) -> str:
    return normalize_uuid_fragment(uuid_value)[-length:].upper()
