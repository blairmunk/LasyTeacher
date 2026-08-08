"""Pure calculations for class journal reports."""

from core_logic.entities.journal import JournalData, JournalSource


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
            cells = [
                self._cell(
                    event,
                    entries.get((student.pk, event.pk)),
                )
                for event in source.events
            ]
            scores = [
                cell['score']
                for cell in cells
                if cell['status'] == 'graded'
            ]
            all_rows.append({
                'student': student,
                'cells': cells,
                'avg_score': (
                    round(sum(scores) / len(scores), 1)
                    if scores
                    else None
                ),
                'score_count': len(scores),
                'debts': sum(
                    1
                    for cell in cells
                    if cell['status'] in ('absent', 'missing')
                ),
            })

        rows = (
            [row for row in all_rows if row['debts'] > 0]
            if show_debts_only
            else all_rows
        )
        return JournalData(
            course=source.course,
            group=source.group,
            events=source.events,
            event_stats=self._event_stats(source.events, all_rows),
            rows=rows,
            all_rows_count=len(all_rows),
            show_debts_only=show_debts_only,
            total_debts=sum(row['debts'] for row in all_rows),
            students_with_debts=sum(
                1 for row in all_rows if row['debts'] > 0
            ),
            courses=source.courses,
        )

    def _cell(self, event, entry):
        participation = entry.participation if entry else None
        mark = entry.mark if entry else None
        cell = {
            'event': event,
            'participation': participation,
            'mark': mark,
            'score': None,
            'status': 'missing',
            'css_class': 'journal-missing',
            'display': '',
            'variant': entry.variant if entry else None,
        }
        if participation is None:
            return cell
        if participation.status == 'absent':
            cell.update(
                status='absent',
                display='Н',
                css_class='journal-absent',
            )
        elif mark is not None and mark.score is not None:
            cell.update(
                status='graded',
                score=mark.score,
                display=str(mark.score),
                css_class=self._score_css(mark.score),
            )
        elif participation.status in ('assigned', 'started'):
            cell.update(
                status='in_progress',
                display='…',
                css_class='journal-progress',
            )
        elif participation.status == 'completed':
            cell.update(
                status='completed',
                display='✓',
                css_class='journal-completed',
            )
        else:
            cell.update(status='assigned', display='–', css_class='')
        return cell

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
                for cell in row['cells']
                if cell['event'].pk == event.pk
            ]
            stats.append({
                'event': event,
                'graded': sum(
                    1 for cell in cells if cell['status'] == 'graded'
                ),
                'absent': sum(
                    1 for cell in cells if cell['status'] == 'absent'
                ),
                'missing': sum(
                    1 for cell in cells if cell['status'] == 'missing'
                ),
                'total': len(cells),
            })
        return stats
