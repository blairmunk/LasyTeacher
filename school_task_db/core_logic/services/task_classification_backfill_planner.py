"""Plan conservative legacy task classification links."""

from collections import defaultdict

from core_logic.entities.task_classification_backfill import (
    TaskClassificationBackfillIssue,
    TaskClassificationBackfillMutation,
    TaskClassificationBackfillPlan,
)


def plan_task_classification_backfill(snapshot):
    content_by_code = defaultdict(list)
    requirements_by_code = defaultdict(list)
    for entry in snapshot.content_entries:
        content_by_code[entry.code].append(entry)
    for requirement in snapshot.requirements:
        requirements_by_code[requirement.code].append(requirement)

    mutations = []
    issues = []
    for task in snapshot.tasks:
        content_codifier_ids = set(task.content_codifier_ids)
        if task.legacy_content_code and not task.content_entry_ids:
            candidates, reason = _content_candidates(
                task,
                content_by_code[task.legacy_content_code],
            )
            if len(candidates) == 1:
                selected = candidates[0]
                mutations.append(TaskClassificationBackfillMutation(
                    task_id=task.pk,
                    relation_type='content',
                    target_id=selected.pk,
                    reason=reason,
                ))
                content_codifier_ids.add(selected.codifier_id)
            else:
                issues.append(_issue(
                    task.pk,
                    'content',
                    task.legacy_content_code,
                    candidates,
                ))

        if task.legacy_requirement_code and not task.requirement_ids:
            candidates = requirements_by_code[task.legacy_requirement_code]
            if content_codifier_ids:
                candidates = [
                    item for item in candidates
                    if item.codifier_id in content_codifier_ids
                ]
            if len(candidates) == 1:
                mutations.append(TaskClassificationBackfillMutation(
                    task_id=task.pk,
                    relation_type='requirement',
                    target_id=candidates[0].pk,
                    reason=(
                        'content_codifier'
                        if content_codifier_ids
                        else 'unique_code'
                    ),
                ))
            else:
                issues.append(_issue(
                    task.pk,
                    'requirement',
                    task.legacy_requirement_code,
                    candidates,
                ))

    return TaskClassificationBackfillPlan(
        mutations=tuple(mutations),
        issues=tuple(issues),
    )


def _content_candidates(task, candidates):
    if task.requirement_codifier_ids:
        matches = [
            item for item in candidates
            if item.codifier_id in task.requirement_codifier_ids
        ]
        if matches:
            candidates = matches
            reason = 'requirement_codifier'
        else:
            reason = 'code'
    else:
        reason = 'code'
    if task.subtopic_id:
        matches = [
            item for item in candidates
            if item.subtopic_id == task.subtopic_id
        ]
        if matches:
            return matches, 'subtopic'
    matches = [item for item in candidates if item.topic_id == task.topic_id]
    if matches:
        return matches, 'topic'
    if len(candidates) == 1:
        return candidates, 'unique_code'
    return candidates, reason


def _issue(task_id, relation_type, code, candidates):
    return TaskClassificationBackfillIssue(
        task_id=task_id,
        relation_type=relation_type,
        code=code,
        status='ambiguous' if candidates else 'unresolved',
        candidate_ids=tuple(item.pk for item in candidates),
    )
