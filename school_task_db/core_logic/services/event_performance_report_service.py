"""Pure calculations for a written event performance report."""

from collections import Counter, defaultdict

from core_logic.entities.event_performance_report import (
    EventPerformanceReportData,
    EventPerformanceReportSource,
    EventReportTaskSummary,
    EventReportSpecificationItem,
    EventReportTeacherNote,
    EventReportTopicSummary,
)


class EventPerformanceReportService:
    WEAK_TOPIC_THRESHOLD = 50

    def build(
        self,
        source: EventPerformanceReportSource,
    ) -> EventPerformanceReportData:
        participants = source.participants
        present = [item for item in participants if item.status != 'absent']
        graded = [item for item in present if item.score is not None]
        scores = [item.score for item in graded if item.score is not None]
        percentages = [
            item.points / item.max_points * 100
            for item in graded
            if item.points is not None and item.max_points
        ]
        task_summaries = self._task_summaries(source)
        weak_topics = self._weak_topics(source)
        common_errors = self._common_errors(source)
        absent_count = len(participants) - len(present)
        grade_counts = Counter(scores)
        pass_percentage = self._percentage(
            sum(1 for score in scores if score >= 3),
            len(scores),
        )
        quality_percentage = self._percentage(
            sum(1 for score in scores if score >= 4),
            len(scores),
        )

        return EventPerformanceReportData(
            event=source.event,
            narrative=source.narrative,
            participants_total=len(participants),
            present_count=len(present),
            absent_count=absent_count,
            graded_count=len(graded),
            average_score=(round(sum(scores) / len(scores), 2) if scores else None),
            average_percentage=(
                round(sum(percentages) / len(percentages), 1)
                if percentages
                else None
            ),
            pass_percentage=pass_percentage,
            quality_percentage=quality_percentage,
            grade_distribution=tuple(
                (score, grade_counts.get(score, 0))
                for score in (5, 4, 3, 2, 1)
            ),
            specification_items=self._specification_items(source),
            teacher_notes=self._teacher_notes(source),
            task_summaries=task_summaries,
            weak_topics=weak_topics,
            common_errors=common_errors,
            suggested_causes=self._suggested_causes(
                task_summaries,
                weak_topics,
            ),
            suggested_recommendations=self._suggested_recommendations(
                weak_topics,
                pass_percentage,
            ),
            suggested_actions=self._suggested_actions(
                absent_count=absent_count,
                weak_topics=weak_topics,
                scores=scores,
            ),
        )

    def _task_summaries(self, source):
        grouped = defaultdict(list)
        for fact in source.task_scores:
            if fact.max_points and fact.points is not None:
                grouped[fact.group_key].append(fact)

        result = []
        for group_key, facts in grouped.items():
            first = min(facts, key=lambda item: item.order)
            failed = [fact for fact in facts if fact.points < fact.max_points]
            percentages = [fact.points / fact.max_points * 100 for fact in facts]
            topic_label = first.topic_name
            if first.subtopic_name:
                topic_label = f'{topic_label}: {first.subtopic_name}'
            result.append(
                EventReportTaskSummary(
                    group_key=group_key,
                    order=first.order,
                    label=f'Задание {first.order}. {topic_label}',
                    topic_name=first.topic_name,
                    subtopic_name=first.subtopic_name,
                    attempts=len(facts),
                    failed_count=len(failed),
                    zero_count=sum(1 for fact in facts if fact.points == 0),
                    error_percentage=self._percentage(len(failed), len(facts)),
                    average_percentage=round(
                        sum(percentages) / len(percentages),
                        1,
                    ),
                    failed_students=tuple(dict.fromkeys(
                        fact.student_name for fact in failed
                    )),
                    comments=tuple(dict.fromkeys(
                        fact.comment.strip()
                        for fact in failed
                        if fact.comment.strip()
                    )),
                )
            )
        return tuple(sorted(result, key=lambda item: item.order))

    def _specification_items(self, source):
        grouped = defaultdict(list)
        for fact in source.specification:
            grouped[fact.order].append(fact)

        items = []
        for facts in grouped.values():
            first = min(facts, key=lambda item: item.order)
            items.append(
                EventReportSpecificationItem(
                    order=first.order,
                    topics=tuple(dict.fromkeys(
                        fact.topic_name
                        for fact in facts
                        if fact.topic_name
                    )),
                    subtopics=tuple(dict.fromkeys(
                        fact.subtopic_name
                        for fact in facts
                        if fact.subtopic_name
                    )),
                    content_elements=tuple(dict.fromkeys(
                        fact.content_element
                        for fact in facts
                        if fact.content_element
                    )),
                    content_element_descriptions=tuple(dict.fromkeys(
                        description
                        for fact in facts
                        for description in fact.content_element_descriptions
                        if description
                    )),
                    requirement_elements=tuple(dict.fromkeys(
                        value
                        for fact in facts
                        for value in (
                            fact.requirement_element,
                            *fact.codifier_requirements,
                        )
                        if value
                    )),
                )
            )
        return tuple(sorted(items, key=lambda item: item.order))

    @staticmethod
    def _teacher_notes(source):
        notes = (
            EventReportTeacherNote(
                student_name=participant.student_name,
                score=participant.score,
                comment=participant.teacher_comment.strip(),
                needs_attention=participant.needs_attention,
            )
            for participant in source.participants
            if participant.teacher_comment.strip()
        )
        return tuple(sorted(
            notes,
            key=lambda note: (
                not note.needs_attention,
                note.score is None,
                note.score if note.score is not None else 6,
                note.student_name,
            ),
        ))

    def _weak_topics(self, source):
        grouped = defaultdict(list)
        for fact in source.task_scores:
            if fact.max_points and fact.points is not None:
                label = fact.topic_name
                if fact.subtopic_name:
                    label = f'{label}: {fact.subtopic_name}'
                grouped[label].append(fact)

        result = []
        for label, facts in grouped.items():
            failed = [fact for fact in facts if fact.points < fact.max_points]
            error_percentage = self._percentage(len(failed), len(facts))
            if error_percentage < self.WEAK_TOPIC_THRESHOLD:
                continue
            percentages = [fact.points / fact.max_points * 100 for fact in facts]
            result.append(
                EventReportTopicSummary(
                    label=label,
                    attempts=len(facts),
                    failed_count=len(failed),
                    error_percentage=error_percentage,
                    average_percentage=round(
                        sum(percentages) / len(percentages),
                        1,
                    ),
                )
            )
        return tuple(sorted(
            result,
            key=lambda item: (-item.error_percentage, item.label),
        ))

    @staticmethod
    def _common_errors(source):
        values = []
        for participant in source.participants:
            values.extend(
                line.strip()
                for line in participant.mistakes_analysis.splitlines()
                if line.strip()
            )
        values.extend(
            fact.comment.strip()
            for fact in source.task_scores
            if fact.comment.strip()
            and fact.points is not None
            and fact.max_points
            and fact.points < fact.max_points
        )
        return tuple(
            value for value, _count in Counter(values).most_common(8)
        )

    @staticmethod
    def _suggested_causes(task_summaries, weak_topics):
        causes = []
        if weak_topics:
            causes.append(
                'Недостаточное усвоение отдельных элементов содержания: '
                + '; '.join(topic.label for topic in weak_topics[:3])
                + '.'
            )
        if any(item.zero_count >= max(2, item.attempts // 3) for item in task_summaries):
            causes.append(
                'Часть обучающихся не владеет способом решения отдельных '
                'типов заданий.'
            )
        if len(weak_topics) >= 3:
            causes.append(
                'Наблюдаются системные пробелы, затрагивающие несколько тем.'
            )
        return tuple(causes)

    @staticmethod
    def _suggested_recommendations(weak_topics, pass_percentage):
        recommendations = []
        if weak_topics:
            recommendations.append(
                'Организовать повторение тем: '
                + '; '.join(topic.label for topic in weak_topics[:4])
                + '.'
            )
        if pass_percentage < 80:
            recommendations.append(
                'Провести дифференцированную работу с обучающимися, '
                'не достигшими базового уровня.'
            )
        recommendations.append(
            'Разобрать типичные ошибки и включить аналогичные задания '
            'в последующую практику.'
        )
        return tuple(recommendations)

    @staticmethod
    def _suggested_actions(absent_count, weak_topics, scores):
        actions = []
        if weak_topics:
            actions.append('Провести групповую работу над ошибками.')
        if any(score <= 2 for score in scores):
            actions.append(
                'Подготовить индивидуальные задания и назначить повторную '
                'проверку освоения материала.'
            )
        if absent_count:
            actions.append(
                'Организовать выполнение работы для отсутствовавших '
                'обучающихся.'
            )
        return tuple(actions)

    @staticmethod
    def _percentage(value, total):
        return round(value / total * 100, 1) if total else 0
