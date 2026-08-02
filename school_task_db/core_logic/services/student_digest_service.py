"""Pure assembly of printable student grade digests."""

from collections import defaultdict

from core_logic.entities.student_digest import (
    StudentDigestData,
    StudentDigestEntry,
    StudentDigestOptions,
    StudentDigestSource,
    StudentDigestSubject,
)


class StudentDigestService:
    def build(
        self,
        source: StudentDigestSource,
        options: StudentDigestOptions,
    ) -> tuple[StudentDigestData, ...]:
        return tuple(
            self._student_digest(source.group.name, student_source, options)
            for student_source in source.students
            if student_source.entries
        )

    def _student_digest(self, group_name, source, options):
        facts = tuple(
            fact
            for fact in sorted(
                source.entries,
                key=lambda item: (item.subject, item.planned_date, item.event_name),
            )
            if options.include_absences or fact.status != 'absent'
        )
        entries = tuple(
            self._entry(fact, options)
            for fact in facts
        )
        subjects_map = defaultdict(list)
        for entry, fact in zip(entries, facts):
            subjects_map[fact.subject or 'Без предмета'].append(entry)

        subjects = tuple(
            StudentDigestSubject(
                title=title,
                entries=tuple(subject_entries),
                average_score=self._average_score(subject_entries),
            )
            for title, subject_entries in subjects_map.items()
        )
        grades = [entry.score for entry in entries if entry.score is not None]
        focus_items = tuple(dict.fromkeys(
            entry.focus for entry in entries if entry.focus
        ))
        retake_entries = tuple(entry for entry in entries if entry.needs_retake)
        return StudentDigestData(
            student=source.student,
            group_name=group_name,
            subjects=subjects,
            average_score=(round(sum(grades) / len(grades), 2) if grades else None),
            grades_count=len(grades),
            absent_count=sum(1 for entry in entries if entry.status == 'absent'),
            retake_entries=retake_entries,
            focus_items=focus_items,
            teacher_comment_entries=tuple(
                entry for entry in entries if entry.teacher_comment
            ),
        )

    def _entry(self, fact, options):
        focus_parts = []
        if fact.recommendations:
            focus_parts.append(fact.recommendations.strip())
        if fact.mistakes_analysis:
            focus_parts.append(fact.mistakes_analysis.strip())
        if fact.failed_topics:
            focus_parts.append('Повторить: ' + ', '.join(fact.failed_topics))
        if options.include_task_comments:
            focus_parts.extend(
                comment for comment in fact.task_comments if comment
            )
        focus = '; '.join(dict.fromkeys(part for part in focus_parts if part))

        is_absent = fact.status == 'absent'
        low_score = (
            fact.score is not None
            and fact.score <= options.retake_score_threshold
        )
        needs_retake = is_absent or low_score or fact.needs_attention
        if is_absent:
            retake_reason = 'Работа пропущена: необходимо согласовать выполнение.'
        elif low_score:
            retake_reason = 'Рекомендуется повторная подготовка и пересдача.'
        elif fact.needs_attention:
            retake_reason = 'Работа отмечена учителем как требующая внимания.'
        else:
            retake_reason = ''

        return StudentDigestEntry(
            event_id=fact.event_id,
            event_name=fact.event_name,
            work_name=fact.work_name,
            planned_date=fact.planned_date,
            status=fact.status,
            score=fact.score,
            points=fact.points,
            max_points=fact.max_points,
            focus=focus,
            teacher_comment=(
                fact.teacher_comment.strip()
                if options.include_teacher_comments
                else ''
            ),
            needs_retake=needs_retake,
            retake_reason=retake_reason,
        )

    @staticmethod
    def _average_score(entries):
        scores = [entry.score for entry in entries if entry.score is not None]
        return round(sum(scores) / len(scores), 2) if scores else None
