"""Pure calculations for class journal reports."""

from core_logic.entities.journal import (
    JournalCell,
    JournalData,
    JournalEventStat,
    JournalRow,
    JournalSource,
)


class JournalService:
    def build(
        self,
        source: JournalSource,
        show_debts_only: bool = False,
    ) -> JournalData:
        entries = {
            (entry.student_id, entry.event_id): entry
            for entry in source.entries
        }
        all_rows = []
        for student in source.students:
            cells = tuple(
                self._cell(
                    event,
                    entries.get((student.pk, event.pk)),
                )
                for event in source.events
            )
            scores = [
                cell.score
                for cell in cells
                if cell.status == 'graded' and cell.score is not None
            ]
            all_rows.append(JournalRow(
                student=student,
                cells=cells,
                avg_score=(
                    round(sum(scores) / len(scores), 1)
                    if scores
                    else None
                ),
                score_count=len(scores),
                debts=sum(
                    1
                    for cell in cells
                    if cell.status in ('absent', 'missing')
                ),
            ))

        rows = (
            tuple(row for row in all_rows if row.debts > 0)
            if show_debts_only
            else tuple(all_rows)
        )
        return JournalData(
            course=source.course,
            group=source.group,
            events=tuple(source.events),
            event_stats=self._event_stats(source.events, all_rows),
            rows=rows,
            all_rows_count=len(all_rows),
            show_debts_only=show_debts_only,
            total_debts=sum(row.debts for row in all_rows),
            students_with_debts=sum(
                1 for row in all_rows if row.debts > 0
            ),
            courses=tuple(source.courses),
        )

    def _cell(self, event, entry):
        participation = entry.participation if entry else None
        mark = entry.mark if entry else None
        variant = entry.variant if entry else None

        if participation is None:
            return JournalCell(
                event=event,
                participation=None,
                mark=None,
                score=None,
                status='missing',
                css_class='journal-missing',
                display='',
                variant=variant,
            )
        if participation.status == 'absent':
            return JournalCell(
                event=event,
                participation=participation,
                mark=mark,
                score=None,
                status='absent',
                css_class='journal-absent',
                display='Н',
                variant=variant,
            )
        if mark is not None and mark.score is not None:
            return JournalCell(
                event=event,
                participation=participation,
                mark=mark,
                score=mark.score,
                status='graded',
                css_class=self._score_css(mark.score),
                display=str(mark.score),
                variant=variant,
            )
        if participation.status in ('assigned', 'started'):
            return JournalCell(
                event=event,
                participation=participation,
                mark=mark,
                score=None,
                status='in_progress',
                css_class='journal-progress',
                display='…',
                variant=variant,
            )
        if participation.status == 'completed':
            return JournalCell(
                event=event,
                participation=participation,
                mark=mark,
                score=None,
                status='completed',
                css_class='journal-completed',
                display='✓',
                variant=variant,
            )
        return JournalCell(
            event=event,
            participation=participation,
            mark=mark,
            score=None,
            status='assigned',
            css_class='',
            display='–',
            variant=variant,
        )

    @staticmethod
    def _score_css(score):
        if score >= 5:
            return 'journal-5'
        if score == 4:
            return 'journal-4'
        if score == 3:
            return 'journal-3'
        return 'journal-2'

    @staticmethod
    def _event_stats(events, rows):
        stats = []
        for event in events:
            cells = [
                cell
                for row in rows
                for cell in row.cells
                if cell.event.pk == event.pk
            ]
            stats.append(JournalEventStat(
                event=event,
                graded=sum(1 for cell in cells if cell.status == 'graded'),
                absent=sum(1 for cell in cells if cell.status == 'absent'),
                missing=sum(1 for cell in cells if cell.status == 'missing'),
                total=len(cells),
            ))
        return tuple(stats)
