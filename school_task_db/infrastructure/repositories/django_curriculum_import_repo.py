"""Django persistence adapter for curriculum catalog imports."""

from codifier.models import ContentEntry
from core_logic.entities.curriculum_import import (
    CurriculumBindingIssue,
    CurriculumImportDefinition,
    CurriculumImportResult,
)
from core_logic.interfaces.curriculum_import_repo import (
    ICurriculumImportRepository,
)
from curriculum.models import SubTopic, Topic


class DjangoCurriculumImportRepository(ICurriculumImportRepository):
    def apply_curriculum_import(
        self,
        definition: CurriculumImportDefinition,
        clear_existing: bool,
    ) -> CurriculumImportResult:
        topics_deleted = 0
        subtopics_deleted = 0
        if clear_existing:
            topics_to_delete = Topic.objects.filter(
                subject=definition.subject,
                section__in=definition.sections,
            )
            topics_deleted = topics_to_delete.count()
            subtopics_deleted = SubTopic.objects.filter(
                topic__in=topics_to_delete,
            ).count()
            topics_to_delete.delete()

        topic_map = {}
        subtopic_map = {}
        topics_created = 0
        subtopics_created = 0
        for topic_item in definition.topics:
            topic, created = Topic.objects.get_or_create(
                name=topic_item.name,
                subject=definition.subject,
                section=topic_item.section,
                grade_level=topic_item.grade_level,
                defaults={'order': topic_item.order},
            )
            if created:
                topics_created += 1
            elif topic.order != topic_item.order:
                topic.order = topic_item.order
                topic.save(update_fields=['order', 'updated_at'])
            topic_map[topic_item.name] = topic

            for subtopic_item in topic_item.subtopics:
                subtopic, created = SubTopic.objects.get_or_create(
                    topic=topic,
                    name=subtopic_item.name,
                    defaults={'order': subtopic_item.order},
                )
                if created:
                    subtopics_created += 1
                elif subtopic.order != subtopic_item.order:
                    subtopic.order = subtopic_item.order
                    subtopic.save(update_fields=['order', 'updated_at'])
                subtopic_map[subtopic_item.name] = subtopic

        bindings_applied = 0
        issues = []
        for binding in definition.bindings:
            entries = ContentEntry.objects.filter(
                codifier__short_name=binding.codifier_short_name,
                code=binding.content_code,
            )
            entry_count = entries.count()
            if entry_count == 0:
                issues.append(_binding_issue(binding, 'entry_not_found'))
                continue
            if entry_count > 1:
                issues.append(_binding_issue(binding, 'entry_ambiguous'))
                continue

            entry = entries.get()
            entry.topic = topic_map[binding.topic_name]
            entry.subtopic = (
                subtopic_map[binding.subtopic_name]
                if binding.subtopic_name
                else None
            )
            entry.save(update_fields=['topic', 'subtopic', 'updated_at'])
            bindings_applied += 1

        return CurriculumImportResult(
            topics_created=topics_created,
            subtopics_created=subtopics_created,
            topics_deleted=topics_deleted,
            subtopics_deleted=subtopics_deleted,
            bindings_applied=bindings_applied,
            bound_codifier_entries=ContentEntry.objects.filter(
                topic__isnull=False,
            ).count(),
            total_codifier_entries=ContentEntry.objects.count(),
            issues=tuple(issues),
        )


def _binding_issue(binding, reason):
    return CurriculumBindingIssue(
        reason=reason,
        codifier_short_name=binding.codifier_short_name,
        content_code=binding.content_code,
        topic_name=binding.topic_name,
        subtopic_name=binding.subtopic_name,
    )
