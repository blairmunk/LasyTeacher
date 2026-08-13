"""Pure codifier calculations."""

from core_logic.entities.codifier import CodifierCoverage


class CodifierService:
    @staticmethod
    def content_code_sort_key(code: str) -> tuple:
        """Return a natural key so 1.2 sorts before 1.10."""
        return tuple(
            (0, int(part)) if part.isdigit() else (1, part.casefold())
            for part in code.split('.')
        )

    @staticmethod
    def coverage(total: int, covered: int) -> CodifierCoverage:
        if total <= 0:
            return CodifierCoverage()

        covered = max(0, min(covered, total))
        return CodifierCoverage(
            total=total,
            covered=covered,
            uncovered=total - covered,
            pct=round(covered / total * 100),
        )
