"""Web presentation for work and remedial document rendering results."""

from dataclasses import dataclass, field

from django.urls import reverse

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DOCUMENT_RENDER_STATUS_VARIANTS_NOT_REQUIRED,
)


@dataclass(frozen=True)
class JsonResponseSpec:
    payload: dict = field(default_factory=dict)
    status_code: int = 200
    not_found_message: str = ''

    @property
    def is_not_found(self) -> bool:
        return bool(self.not_found_message)


class WorkDocumentWebPresenter:
    def work_document_response(
        self,
        result,
        render_target,
        print_overrides,
    ) -> JsonResponseSpec:
        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            return JsonResponseSpec(not_found_message='Работа не найдена')
        if result.status == DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED:
            return self._work_error(
                'Для работы над ошибками используйте печать '
                'персональных листов.',
                status_code=400,
            )
        if result.status == DOCUMENT_RENDER_STATUS_VARIANTS_NOT_REQUIRED:
            return self._work_error(
                'Для этой работы документ не формируется: '
                'используется внешний материал.',
                status_code=400,
            )
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            return self._work_error(
                f'Неподдерживаемый тип рендера: {result.renderer_type}',
                status_code=400,
            )
        if not result.success:
            return self._work_error(
                'Не удалось сформировать документ.',
                status_code=500,
            )

        files = [
            {
                'name': file_info.filename,
                'size': f'{file_info.size_kb:.1f} KB',
                'download_url': self._download_url(
                    result.file_type,
                    file_info.filename,
                ),
            }
            for file_info in result.files
        ]
        return JsonResponseSpec(payload={
            'success': True,
            'message': (
                f'{render_target.file_type_label} документ создан '
                f'({self._work_content_description(print_overrides)})'
            ),
            'files': files,
            'total_files': len(files),
        })

    def remedial_sheet_response(self, result) -> JsonResponseSpec:
        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            return JsonResponseSpec(not_found_message='Вариант не найден')
        if result.status == DOCUMENT_RENDER_STATUS_NOT_REMEDIAL:
            return self._remedial_error(
                'Этот вариант не является работой над ошибками',
                status_code=400,
            )
        if result.status == DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED:
            return self._remedial_error(
                'Лист работы над ошибками не привязан к ученику',
                status_code=400,
            )
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            return self._remedial_error(
                f'Неподдерживаемый тип рендера: {result.renderer_type}',
                status_code=400,
            )
        if result.status == DOCUMENT_RENDER_STATUS_EMPTY:
            return self._remedial_error(
                'Файлы не были созданы',
                status_code=500,
            )
        if not result.success:
            return self._remedial_error(
                'Не удалось сформировать лист работы над ошибками.',
                status_code=500,
            )

        return JsonResponseSpec(payload={
            'status': 'success',
            'files': [
                {
                    'filename': file_info.filename,
                    'url': self._download_url(
                        result.file_type,
                        file_info.filename,
                    ),
                }
                for file_info in result.files
            ],
            'message': (
                f'Рабочий лист создан '
                f'({result.renderer_type.upper()})'
            ),
        })

    def remedial_sheet_batch_response(self, result) -> JsonResponseSpec:
        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            return JsonResponseSpec(not_found_message='Работа не найдена')
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            return self._batch_error(
                f'Неподдерживаемый тип рендера: {result.renderer_type}',
                status_code=400,
            )
        if result.status == DOCUMENT_RENDER_STATUS_EMPTY:
            return self._batch_error(
                'В этой работе нет персональных листов '
                'работы над ошибками для печати.',
                status_code=400,
            )
        if not result.success:
            return self._batch_error(
                'Не удалось создать листы работы над ошибками.',
                status_code=500,
            )

        files = [
            {
                'name': file_info.filename,
                'size': f'{file_info.size_kb:.1f} KB',
                'download_url': self._download_url(
                    result.file_type,
                    file_info.filename,
                ),
            }
            for file_info in result.files
        ]
        return JsonResponseSpec(payload={
            'success': True,
            'message': (
                'Пакет листов работы над ошибками создан '
                f'({result.renderer_type.upper()})'
            ),
            'files': files,
            'total_files': len(files),
        })

    def work_exception_response(self, error) -> JsonResponseSpec:
        return self._work_error(str(error), status_code=500)

    def remedial_exception_response(self, error) -> JsonResponseSpec:
        return self._remedial_error(
            f'Ошибка: {error}',
            status_code=500,
        )

    def remedial_batch_exception_response(self, error) -> JsonResponseSpec:
        return self._batch_error(str(error), status_code=500)

    @staticmethod
    def render_status_payload():
        return {
            'status': 'ready',
            'message': 'Система готова к рендерингу',
        }

    @staticmethod
    def _work_content_description(print_overrides):
        if print_overrides.append_answers:
            return 'по спецификации + ответы в конце'
        return 'по спецификации'

    @staticmethod
    def _work_error(message, status_code):
        return JsonResponseSpec(
            payload={'success': False, 'error': str(message)},
            status_code=status_code,
        )

    @staticmethod
    def _remedial_error(message, status_code):
        return JsonResponseSpec(
            payload={'status': 'error', 'message': str(message)},
            status_code=status_code,
        )

    @staticmethod
    def _batch_error(message, status_code):
        return JsonResponseSpec(
            payload={'success': False, 'error': str(message)},
            status_code=status_code,
        )

    @staticmethod
    def _download_url(file_type, filename):
        return reverse(
            'works:download_rendered_file',
            kwargs={
                'file_type': file_type,
                'filename': filename,
            },
        )
