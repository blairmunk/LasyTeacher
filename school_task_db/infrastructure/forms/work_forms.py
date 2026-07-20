"""Infrastructure helpers for Django work forms."""

from django.urls import reverse

from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentRequest
from core_logic.use_cases.compose_work_variants import ComposeWorkVariantsRequest
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
)
from core_logic.value_objects.document_render_options import (
    build_remedial_sheet_render_options,
    build_work_render_options,
    renderer_type_from_data,
)
from infrastructure.forms.work_django_forms import WorkAnalogGroupFormSet
from works.models import Work


class WorkFormAdapter:
    def _get_work_instance(self, work_id=None):
        if not work_id:
            return None
        return Work.objects.filter(pk=work_id).first()

    def build_analog_group_formset(self, data=None, instance=None, work_id=None):
        if instance is None:
            instance = self._get_work_instance(work_id)
        if data is not None:
            return WorkAnalogGroupFormSet(data, instance=instance)
        return WorkAnalogGroupFormSet(instance=instance)

    def work_params_from_form(self, form, work_id=''):
        return CreateWorkParams(
            work_id=work_id,
            name=form.cleaned_data['name'],
            work_type=form.cleaned_data.get('work_type', 'test'),
            duration=form.cleaned_data.get('duration') or 45,
            max_score=form.cleaned_data.get('max_score') or 0,
        )

    def work_form_initial(self, work):
        return {
            'name': work.name,
            'work_type': work.work_type,
            'duration': work.duration,
            'max_score': work.max_score,
        }

    def work_specs_from_formset(self, formset, work_id):
        specs = []
        for row in formset.cleaned_data:
            if not row or row.get('DELETE'):
                continue

            analog_group = row.get('analog_group')
            if not analog_group:
                continue

            specs.append(
                CreateWorkAnalogGroupParams(
                    work_id=work_id,
                    analog_group_id=str(analog_group.pk),
                    order=row.get('order') or 0,
                    count=row.get('count') or 1,
                    weight=row.get('weight') or 1,
                )
            )
        return specs

    def compose_variants_request_from_form(self, form, work_id):
        return ComposeWorkVariantsRequest(
            work_id=work_id,
            count=form.cleaned_data['count'],
        )

    def render_work_document_request_from_post(self, post_data, work_id):
        return RenderWorkDocumentRequest(
            work_id=work_id,
            options=build_work_render_options(post_data),
        )

    def document_renderer_type_from_post(self, post_data, default='pdf'):
        return renderer_type_from_data(post_data, default=default)

    def render_remedial_sheet_request_from_post(self, post_data, variant_id):
        return RenderRemedialSheetDocumentRequest(
            variant_id=variant_id,
            options=build_remedial_sheet_render_options(post_data),
        )

    def rendered_document_file_request(self, file_type, filename):
        return GetRenderedDocumentFileRequest(
            file_type=file_type,
            filename=filename,
        )

    def rendered_work_document_response_payload(self, result, options):
        files_info = [
            {
                'name': file_info.filename,
                'size': f'{file_info.size_kb:.1f} KB',
                'download_url': reverse(
                    'works:download_rendered_file',
                    kwargs={
                        'file_type': result.file_type,
                        'filename': file_info.filename,
                    },
                ),
            }
            for file_info in result.files
        ]

        return {
            'success': True,
            'message': (
                f'{options.file_type_label} документ создан '
                f'({options.content_description})'
            ),
            'files': files_info,
            'total_files': len(files_info),
        }

    def remedial_sheet_response_payload(self, result):
        return {
            'status': 'success',
            'files': [
                {
                    'filename': file_info.filename,
                    'url': reverse(
                        'works:download_rendered_file',
                        kwargs={
                            'file_type': result.file_type,
                            'filename': file_info.filename,
                        },
                    ),
                }
                for file_info in result.files
            ],
            'message': (
                f'Рабочий лист создан '
                f'({result.renderer_type.upper()})'
            ),
        }
