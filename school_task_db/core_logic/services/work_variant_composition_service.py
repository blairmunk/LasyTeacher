"""Build immutable variant creation plans from a work specification."""

import random
from dataclasses import replace
from typing import Callable

from core_logic.entities.work import VariantGenerationGroup
from core_logic.entities.work_variant_composition import (
    VariantContentBlockCreationPlan,
    VariantCreationPlan,
    VariantTaskCreationPlan,
    WorkVariantCompositionInput,
    WorkVariantCompositionPlan,
    WorkVariantCompositionSource,
    WorkVariantContentBlock,
    WorkVariantSpecRow,
)
from core_logic.services.work_score_allocation_service import (
    WorkScoreAllocationService,
    WorkScoreSpecRow,
)
from core_logic.value_objects.work_content_plan import (
    WORK_CONTENT_TEXT,
)
from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_ANY


class WorkVariantCompositionService:
    def __init__(
        self,
        task_selector: Callable | None = None,
        score_allocation_service=None,
    ):
        self.task_selector = task_selector or random.sample
        self.score_allocation_service = (
            score_allocation_service or WorkScoreAllocationService()
        )

    def build_input(
        self,
        source: WorkVariantCompositionSource,
    ) -> WorkVariantCompositionInput:
        return WorkVariantCompositionInput(
            work_name=source.work_name,
            duration=source.duration,
            max_score=source.max_score,
            effective_max_score=self.score_allocation_service.effective_max_score(
                max_score=source.max_score,
                spec_rows=source.spec_rows,
            ),
            variant_counter=source.variant_counter,
            spec_rows=tuple(
                WorkVariantSpecRow(
                    spec_row_id=row.spec_row_id,
                    count=row.count,
                    weight=row.weight,
                    content_order=row.content_order,
                    available_tasks=tuple(
                        task
                        for task in row.available_tasks
                        if self.bank_role_matches(
                            task.bank_role,
                            row.bank_role_filter,
                        )
                    ),
                    render_mode=row.render_mode,
                    is_assessable=row.is_assessable,
                    blank_cells_after=row.blank_cells_after,
                    blank_space_area_cm2=row.blank_space_area_cm2,
                    page_break_after=row.page_break_after,
                )
                for row in source.spec_rows
            ),
            content_blocks=source.content_blocks,
        )

    @staticmethod
    def build_generation_groups(sources):
        return [
            VariantGenerationGroup(
                group_name=source.group_name,
                requested_count=source.requested_count,
                available_count=sum(
                    1
                    for role in source.task_bank_roles
                    if WorkVariantCompositionService.bank_role_matches(
                        role,
                        source.bank_role_filter,
                    )
                ),
                bank_role_filter=source.bank_role_filter,
            )
            for source in sources
        ]

    @classmethod
    def build_work_detail_groups(cls, groups):
        return [
            replace(
                group,
                available_count=sum(
                    1
                    for role in group.task_bank_roles
                    if cls.bank_role_matches(role, group.bank_role_filter)
                ),
            )
            for group in groups
        ]

    @staticmethod
    def bank_role_matches(task_role, bank_role_filter):
        return (
            bank_role_filter == TASK_BANK_ROLE_ANY
            or task_role == bank_role_filter
        )

    def compose(
        self,
        composition_input: WorkVariantCompositionInput,
        count: int,
    ) -> WorkVariantCompositionPlan:
        if count < 1:
            raise ValueError('count must be positive')

        score_allocations = self.score_allocation_service.allocate(
            max_score=composition_input.max_score,
            spec_rows=(
                WorkScoreSpecRow(
                    spec_row_id=row.spec_row_id,
                    count=row.count,
                    weight=row.weight,
                    is_assessable=row.is_assessable,
                )
                for row in composition_input.spec_rows
            ),
        )
        variants = tuple(
            self._compose_variant(
                composition_input,
                number=composition_input.variant_counter + offset,
                score_allocations=score_allocations,
            )
            for offset in range(1, count + 1)
        )
        return WorkVariantCompositionPlan(
            variants=variants,
            next_variant_counter=composition_input.variant_counter + count,
        )

    def _compose_variant(
        self,
        composition_input,
        number,
        score_allocations,
    ):
        tasks = []
        score_index = 0
        task_order = 1
        for row in composition_input.spec_rows:
            selected_tasks = self._select_tasks(row)
            for task in selected_tasks:
                max_points = (
                    score_allocations[score_index].points
                    if score_index < len(score_allocations)
                    else 0
                )
                tasks.append(
                    VariantTaskCreationPlan(
                        task_id=task.task_id,
                        source_selection_id=row.spec_row_id,
                        content_order=row.content_order,
                        order=task_order,
                        max_points=max_points,
                        weight=row.weight,
                        bank_role=task.bank_role,
                        render_mode=row.render_mode,
                        is_assessable=row.is_assessable,
                        blank_cells_after=row.blank_cells_after,
                        blank_space_area_cm2=row.blank_space_area_cm2,
                        page_break_after=row.page_break_after,
                    )
                )
                task_order += 1
                score_index += 1

        return VariantCreationPlan(
            number=number,
            work_name_snapshot=composition_input.work_name,
            max_score_snapshot=composition_input.effective_max_score,
            duration_snapshot=composition_input.duration,
            tasks=tuple(tasks),
            content_blocks=tuple(
                VariantContentBlockCreationPlan(
                    source_content_id=block.source_content_id,
                    content_type=block.content_type,
                    order=block.order,
                    title=block.title,
                    content=_variant_content_snapshot(block),
                )
                for block in composition_input.content_blocks
            ),
        )

    def _select_tasks(self, row):
        if len(row.available_tasks) < row.count:
            return row.available_tasks
        return tuple(self.task_selector(row.available_tasks, row.count))


def _variant_content_snapshot(block: WorkVariantContentBlock):
    if block.content_type == WORK_CONTENT_TEXT:
        return {'body': block.body}
    return {
        'topics': [
            {
                'id': topic.topic_id,
                'name': topic.name,
                'subject': topic.subject,
                'section': topic.section,
                'grade_level': topic.grade_level,
                'content': topic.content,
                'subtopics': [
                    {
                        'id': subtopic.subtopic_id,
                        'name': subtopic.name,
                        'content': subtopic.content,
                    }
                    for subtopic in topic.subtopics
                    if (
                        block.include_subtopics
                        and subtopic.content
                    )
                ],
            }
            for topic in block.topics
            if topic.content
        ],
        'include_subtopics': block.include_subtopics,
    }
