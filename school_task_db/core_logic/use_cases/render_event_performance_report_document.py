"""Render a sectioned document for one event performance report."""

from dataclasses import dataclass, field, replace

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DocumentRenderResult,
)
from core_logic.interfaces.presentation_profile_repo import (
    IPresentationProfileRepository,
)
from core_logic.use_cases.presentation_profile_selection import (
    resolve_document_presentation_profile,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan_factories import (
    build_event_report_document_recipe_for_render,
    build_event_report_document_source,
)
from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
)
from core_logic.value_objects.report_document_options import (
    EventReportDocumentOptions,
)


@dataclass(frozen=True)
class RenderEventPerformanceReportDocumentRequest:
    event_id: str
    render_target: RenderTarget
    presentation_profile: DocumentPresentationProfile | None = None
    presentation_profile_id: str = ''
    options: EventReportDocumentOptions = field(
        default_factory=EventReportDocumentOptions,
    )


class RenderEventPerformanceReportDocumentUseCase:
    def __init__(
        self,
        get_event_report_use_case,
        render_document_from_recipe_use_case: RenderDocumentFromRecipeUseCase,
        presentation_profile_repo: IPresentationProfileRepository | None = None,
    ):
        self.get_event_report_use_case = get_event_report_use_case
        self.render_document_from_recipe_use_case = (
            render_document_from_recipe_use_case
        )
        self.presentation_profile_repo = presentation_profile_repo

    def execute(self, request):
        report = self.get_event_report_use_case.execute(request.event_id)
        if report is None:
            return DocumentRenderResult(
                status=DOCUMENT_RENDER_STATUS_NOT_FOUND,
                renderer_type=request.render_target.renderer_type,
            )
        options = request.options
        if not report.event.has_task_level_results:
            options = replace(
                options,
                include_specification=False,
                include_task_analysis=False,
                include_content_element_text=False,
            )

        return self.render_document_from_recipe_use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=build_event_report_document_source(
                    event_id=request.event_id,
                    event_name=report.event.name,
                ),
                recipe=build_event_report_document_recipe_for_render(
                    options=options,
                    presentation_profile=resolve_document_presentation_profile(
                        document_type=(
                            EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE
                        ),
                        request_presentation_profile=(
                            request.presentation_profile
                        ),
                        request_presentation_profile_id=(
                            request.presentation_profile_id
                        ),
                        presentation_profile_repo=(
                            self.presentation_profile_repo
                        ),
                    ),
                ),
                render_target=request.render_target,
                source_name=report.event.name,
            )
        )
