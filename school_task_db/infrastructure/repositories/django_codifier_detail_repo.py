"""Django read adapter for codifier structure and coverage."""

from collections import defaultdict

from django.db.models import Count, Q

from core_logic.entities.codifier import (
    CodifierContentEntry,
    CodifierDetailSpec,
    CodifierObjectRef,
    CodifierRequirement,
    CodifierSiblingCode,
)
from core_logic.interfaces.codifier_detail_repo import ICodifierDetailRepository
from core_logic.services.codifier_service import CodifierService
from codifier.models import CodifierSpec, ContentEntry, Requirement


class DjangoCodifierDetailRepository(ICodifierDetailRepository):
    def get_codifier(self, codifier_id: str):
        codifier = CodifierSpec.objects.prefetch_related(
            'content_entries',
            'requirements',
        ).filter(pk=codifier_id).first()
        if codifier is None:
            return None

        return CodifierDetailSpec(
            pk=str(codifier.pk),
            short_name=codifier.short_name,
            name=codifier.name,
            content_entries_count=codifier.content_entries.count(),
        )

    def get_content_tree(self, codifier_id: str):
        entries = list(
            ContentEntry.objects.filter(codifier_id=codifier_id)
            .select_related('topic', 'subtopic')
            .annotate(
                topic_task_count=Count('topic__task', distinct=True),
                subtopic_task_count=Count('subtopic__task', distinct=True),
            )
        )
        children_by_parent = defaultdict(list)
        for entry in entries:
            children_by_parent[entry.parent_id].append(entry)
        for children in children_by_parent.values():
            children.sort(
                key=lambda item: CodifierService.content_code_sort_key(
                    item.code,
                )
            )

        sibling_codes = self._get_sibling_codes(entries)
        return tuple(
            self._build_content_entry(
                entry,
                children_by_parent=children_by_parent,
                sibling_codes=sibling_codes,
            )
            for entry in children_by_parent[None]
        )

    def get_requirements(self, codifier_id: str):
        return tuple(
            CodifierRequirement(
                code=requirement.code,
                name=requirement.name,
                cognitive_level=requirement.cognitive_level,
                cognitive_level_display=(
                    requirement.get_cognitive_level_display()
                    if requirement.cognitive_level
                    else ''
                ),
                task_count=requirement.task_count,
            )
            for requirement in Requirement.objects.filter(
                codifier_id=codifier_id,
            ).annotate(task_count=Count('tasks'))
        )

    def get_coverage(self, codifier_id: str) -> dict:
        leaves = ContentEntry.objects.filter(
            codifier_id=codifier_id,
            children__isnull=True,
        )
        total = leaves.count()
        covered = leaves.filter(
            Q(
                subtopic__isnull=False,
                subtopic__task__isnull=False,
            )
            | Q(
                subtopic__isnull=True,
                topic__task__isnull=False,
            )
        ).distinct().count()
        return CodifierService.coverage(total=total, covered=covered)

    def _build_content_entry(
        self,
        entry,
        *,
        children_by_parent,
        sibling_codes,
    ):
        return CodifierContentEntry(
            code=entry.code,
            name=entry.name,
            topic=(
                CodifierObjectRef(name=entry.topic.name)
                if entry.topic
                else None
            ),
            subtopic=(
                CodifierObjectRef(name=entry.subtopic.name)
                if entry.subtopic
                else None
            ),
            grade_studied=entry.grade_studied,
            task_count=(
                entry.subtopic_task_count
                if entry.subtopic_id
                else entry.topic_task_count
            ),
            sibling_codes=tuple(
                CodifierSiblingCode(
                    codifier=CodifierObjectRef(
                        short_name=sibling.codifier.short_name,
                    ),
                    code=sibling.code,
                )
                for sibling in sibling_codes.get(entry.pk, [])
            ),
            children=tuple(
                self._build_content_entry(
                    child,
                    children_by_parent=children_by_parent,
                    sibling_codes=sibling_codes,
                )
                for child in children_by_parent[entry.pk]
            ),
        )

    @staticmethod
    def _get_sibling_codes(entries):
        topic_ids = {entry.topic_id for entry in entries if entry.topic_id}
        subtopic_ids = {
            entry.subtopic_id for entry in entries if entry.subtopic_id
        }
        if not topic_ids and not subtopic_ids:
            return {}

        candidates = ContentEntry.objects.filter(
            Q(topic_id__in=topic_ids) | Q(subtopic_id__in=subtopic_ids)
        ).select_related('codifier')
        by_topic = defaultdict(list)
        by_subtopic = defaultdict(list)
        for candidate in candidates:
            if candidate.topic_id:
                by_topic[candidate.topic_id].append(candidate)
            if candidate.subtopic_id:
                by_subtopic[candidate.subtopic_id].append(candidate)

        result = {}
        for entry in entries:
            if entry.subtopic_id:
                matches = by_subtopic[entry.subtopic_id]
            elif entry.topic_id:
                matches = by_topic[entry.topic_id]
            else:
                matches = []
            result[entry.pk] = [
                candidate
                for candidate in matches
                if candidate.pk != entry.pk
            ]
        return result
