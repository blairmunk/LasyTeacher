"""Build data for rendering a remedial sheet."""

from core_logic.entities.work import RemedialSheetData
from core_logic.interfaces.remedial_sheet_repo import IRemedialSheetRepository
from core_logic.services.remedial_sheet_service import RemedialSheetService


class GetRemedialSheetDataUseCase:
    def __init__(
        self,
        remedial_repo: IRemedialSheetRepository,
        sheet_service: RemedialSheetService | None = None,
    ):
        self.remedial_repo = remedial_repo
        self.sheet_service = sheet_service or RemedialSheetService()

    def execute(self, variant_id: str) -> RemedialSheetData:
        source = self.remedial_repo.get_remedial_sheet_source(variant_id)
        if source is None:
            return RemedialSheetData(
                variant=None,
                student=None,
                source_work=None,
                mark=None,
                status='not_found',
                message='Вариант не найден.',
            )
        sheet_data = self.sheet_service.build(source)

        if not sheet_data.source_work:
            variant = sheet_data.variant
            work_id = str(variant.work.pk) if getattr(variant, 'work', None) else ''
            return RemedialSheetData(
                variant=sheet_data.variant,
                student=sheet_data.student,
                source_work=sheet_data.source_work,
                mark=sheet_data.mark,
                original_tasks=sheet_data.original_tasks,
                new_tasks=sheet_data.new_tasks,
                content_blocks=sheet_data.content_blocks,
                status='missing_source',
                message='У этого варианта нет исходной работы.',
                redirect_work_id=work_id,
            )
        if not sheet_data.student:
            return RemedialSheetData(
                variant=sheet_data.variant,
                student=sheet_data.student,
                source_work=sheet_data.source_work,
                mark=sheet_data.mark,
                original_tasks=sheet_data.original_tasks,
                new_tasks=sheet_data.new_tasks,
                content_blocks=sheet_data.content_blocks,
                status='missing_student',
                message=(
                    'Для разбора ошибок нужно знать ученика, '
                    'которому назначен вариант.'
                ),
            )

        return sheet_data
