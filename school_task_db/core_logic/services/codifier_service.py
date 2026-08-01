"""Pure codifier calculations."""


class CodifierService:
    @staticmethod
    def content_code_sort_key(code: str) -> tuple:
        """Return a natural key so 1.2 sorts before 1.10."""
        return tuple(
            (0, int(part)) if part.isdigit() else (1, part.casefold())
            for part in code.split('.')
        )

    @staticmethod
    def coverage(total: int, covered: int) -> dict:
        if total <= 0:
            return {
                'total': 0,
                'covered': 0,
                'uncovered': 0,
                'pct': 0,
            }

        covered = max(0, min(covered, total))
        return {
            'total': total,
            'covered': covered,
            'uncovered': total - covered,
            'pct': round(covered / total * 100),
        }
