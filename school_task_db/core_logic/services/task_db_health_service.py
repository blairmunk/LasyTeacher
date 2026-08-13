"""Pure calculations for task database diagnostics."""

from collections import Counter

from core_logic.entities.task_db_health import (
    TaskCountRatio,
    TaskCoverageIssue,
    TaskDBHealthData,
    TaskDBHealthSummary,
    TaskDBHealthSource,
    TaskDBIssueCollection,
    TaskDBStats,
    TaskDifficultyDistribution,
    TaskGroupSizeDistribution,
    TaskTypeDistribution,
)


class TaskDBHealthService:
    def build(
        self,
        source: TaskDBHealthSource,
    ) -> TaskDBHealthData:
        empty_groups = [
            item.group for item in source.group_sizes if item.task_count == 0
        ]
        fragile_groups = [
            item.group for item in source.group_sizes if item.task_count == 1
        ]
        coverage_issues = [
            TaskCoverageIssue(
                work=item.work,
                group=item.group,
                needed=item.needed,
                available=item.available,
                deficit=item.needed - item.available,
            )
            for item in source.coverage
            if item.available < item.needed
        ]
        health_counts = {
            'orphan_variants': source.orphan_variants_count,
            'empty_groups': len(empty_groups),
            'coverage_issues': len(coverage_issues),
            'ungrouped_tasks': source.ungrouped_tasks_count,
            'fragile_groups': len(fragile_groups),
            'works_no_variants': source.works_no_variants_count,
            'works_no_spec': source.works_no_spec_count,
        }
        return TaskDBHealthData(
            stats=TaskDBStats(
                total_tasks=source.total_tasks,
                total_groups=len(source.group_sizes),
                total_works=source.total_works,
                total_variants=source.total_variants,
            ),
            orphan_variants=TaskDBIssueCollection(
                count=source.orphan_variants_count,
                items=source.orphan_variant_samples,
            ),
            empty_groups=TaskDBIssueCollection(
                count=len(empty_groups),
                items=tuple(empty_groups[:20]),
            ),
            coverage_issues=TaskDBIssueCollection(
                count=len(coverage_issues),
                items=tuple(coverage_issues[:20]),
            ),
            difficulty_dist=tuple(
                TaskDifficultyDistribution(
                    difficulty=int(item.key or 0),
                    count=item.count,
                    pct=self._pct(item.count, source.total_tasks),
                )
                for item in source.difficulty_counts
            ),
            ungrouped_tasks=TaskCountRatio(
                count=source.ungrouped_tasks_count,
                pct=self._pct(
                    source.ungrouped_tasks_count,
                    source.total_tasks,
                ),
            ),
            fragile_groups=TaskDBIssueCollection(
                count=len(fragile_groups),
                items=tuple(fragile_groups[:20]),
            ),
            works_no_variants=TaskDBIssueCollection(
                count=source.works_no_variants_count,
                items=source.works_no_variant_samples,
            ),
            works_no_spec=TaskDBIssueCollection(
                count=source.works_no_spec_count,
                items=source.works_no_spec_samples,
            ),
            type_dist=tuple(
                TaskTypeDistribution(
                    task_type=str(item.key or ''),
                    count=item.count,
                    label=str(item.label or item.key or '—'),
                    pct=self._pct(item.count, source.total_tasks),
                )
                for item in source.type_counts
            ),
            most_used_tasks=source.most_used_tasks,
            group_sizes=self._task_group_size_distribution(source.group_sizes),
            unverified_tasks=TaskCountRatio(
                count=source.unverified_tasks_count,
                pct=self._pct(
                    source.unverified_tasks_count,
                    source.total_tasks,
                ),
            ),
            no_source_tasks=TaskCountRatio(
                count=source.no_source_tasks_count,
                pct=self._pct(
                    source.no_source_tasks_count,
                    source.total_tasks,
                ),
            ),
            no_grade_tasks=TaskCountRatio(
                count=source.no_grade_tasks_count,
                pct=self._pct(
                    source.no_grade_tasks_count,
                    source.total_tasks,
                ),
            ),
            health=self._health_summary(health_counts),
            courses=source.courses,
        )

    @staticmethod
    def _task_group_size_distribution(group_sizes):
        counts = Counter(item.task_count for item in group_sizes)
        return tuple(
            TaskGroupSizeDistribution(
                task_count=task_count,
                group_count=counts[task_count],
            )
            for task_count in sorted(counts)
        )

    def _health_summary(self, counts):
        issues = sum(counts.values())
        if issues == 0:
            label, color, icon = 'Отлично', 'success', 'check-circle'
        elif issues <= 5:
            label, color, icon = 'Хорошо', 'info', 'info-circle'
        elif issues <= 15:
            label, color, icon = (
                'Есть замечания',
                'warning',
                'exclamation-triangle',
            )
        else:
            label, color, icon = (
                'Требует внимания',
                'danger',
                'exclamation-circle',
            )
        return TaskDBHealthSummary(
            label=label,
            color=color,
            icon=icon,
            issues=issues,
            issues_text=self._issues_text(issues),
        )

    @staticmethod
    def _issues_text(issues):
        if 11 <= issues % 100 <= 19:
            return f'{issues} замечаний'
        if issues % 10 == 1:
            return f'{issues} замечание'
        if 2 <= issues % 10 <= 4:
            return f'{issues} замечания'
        return f'{issues} замечаний'

    @staticmethod
    def _pct(value, total):
        return round(value / total * 100, 1) if total else 0
