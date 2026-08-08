"""Infrastructure helpers for Django work forms."""

from django.urls import reverse
from django.core.paginator import Paginator

from core_logic.interfaces.work_repo import (
    CreateWorkParams,
    WorkContentBlockParams,
    WorkTaskSelectionParams,
)
from core_logic.entities.work import WorkListFilters
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
)
from core_logic.use_cases.render_remedial_sheet_batch_document import (
    RenderRemedialSheetBatchDocumentRequest,
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
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_RENDER_MODE_TASK_ONLY,
)
from infrastructure.forms.work_django_forms import (
    WorkAnalogGroupFormSet,
    WorkContentBlockFormSet,
)
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

    def build_content_block_formset(
        self,
        data=None,
        instance=None,
        work_id=None,
    ):
        if instance is None:
            instance = self._get_work_instance(work_id)
        kwargs = {
            'instance': instance,
            'prefix': 'content_blocks',
        }
        if data is not None:
            kwargs['data'] = data
        return WorkContentBlockFormSet(**kwargs)

    def work_params_from_form(self, form, work_id=''):
        return CreateWorkParams(
            work_id=work_id,
            name=form.cleaned_data['name'],
            work_type=form.cleaned_data.get('work_type', 'test'),
            assessment_mode=form.cleaned_data['assessment_mode'],
            duration=form.cleaned_data.get('duration') or 45,
            max_score=form.cleaned_data.get('max_score') or 0,
        )

    def work_form_initial(self, work):
        return {
            'name': work.name,
            'work_type': work.work_type,
            'assessment_mode': work.assessment_mode,
            'duration': work.duration,
            'max_score': work.max_score,
        }

    def work_list_filters_from_query(self, query_data):
        return WorkListFilters(
            q=query_data.get('q', '').strip(),
            work_type=query_data.get('work_type', '').strip(),
            variant_status=query_data.get('variant_status', '').strip(),
            hide_remedial=query_data.get('hide_remedial') == '1',
        )

    def work_list_context(self, list_data):
        filters = list_data.filters or WorkListFilters()
        return {
            'works': list_data.works,
            'filters': filters,
            'has_active_filters': filters.has_active_filters,
            'work_type_options': [
                {'value': value, 'label': label}
                for value, label in Work.WORK_TYPE_CHOICES
            ],
            'variant_status_options': [
                {'value': 'with_variants', 'label': 'С вариантами'},
                {'value': 'without_variants', 'label': 'Без вариантов'},
            ],
        }

    def work_detail_context(self, detail):
        content_plan = getattr(detail, 'content_plan', None)
        return {
            'work': detail.work,
            'object': detail.work,
            'variants': detail.variants,
            'analog_groups': detail.analog_groups,
            'spec_preview': detail.spec_preview,
            'content_plan': content_plan,
            'content_blocks': [
                block
                for block in getattr(content_plan, 'blocks', ())
                if block.content_type in ('theory', 'text')
            ],
            'work_presentation_profiles': detail.work_presentation_profiles,
            'remedial_sheet_presentation_profiles': (
                detail.remedial_sheet_presentation_profiles
            ),
            'show_sync_button': detail.show_sync_button,
        }

    def work_create_context(
        self,
        form,
        formset,
        form_data,
        content_formset=None,
    ):
        return {
            'form': form,
            'formset': formset,
            'content_formset': content_formset,
            'analog_group_options': form_data.analog_group_options,
        }

    def work_update_context(
        self,
        work,
        form,
        formset,
        form_data,
        content_formset=None,
    ):
        context = self.work_create_context(
            form,
            formset,
            form_data,
            content_formset=content_formset,
        )
        context['object'] = work
        return context

    def compose_variants_context(self, form_data, form):
        return {
            'work': form_data.work,
            'work_groups': form_data.work_groups,
            'form': form,
        }

    def variant_list_context(self, list_data, query, paginate_by):
        page_obj = Paginator(list_data.variants, paginate_by).get_page(
            query.get('page'),
        )
        return {
            'variants': page_obj.object_list,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
        }

    def variant_detail_context(self, detail):
        return {
            'variant': detail.variant,
            'object': detail.variant,
            'variant_tasks': detail.variant_tasks,
            'total_max_points': detail.total_max_points,
        }

    def orphan_variant_list_context(self, list_data, query, paginate_by):
        context = self.variant_list_context(list_data, query, paginate_by)
        context['total_orphans'] = list_data.total_orphans
        return context

    def variant_delete_context(self, delete_info):
        return {
            'delete_info': delete_info,
            'task_count': delete_info.task_count,
            'has_grades': delete_info.has_participations,
            'grade_count': delete_info.participation_count,
        }

    def bulk_delete_variants_response_payload(self, result):
        return {
            'success': True,
            'deleted': result.deleted_count,
            'remaining': result.remaining_count,
        }

    def render_work_unsupported_renderer_payload(self, renderer_type):
        return {
            'success': False,
            'error': f'Неподдерживаемый тип рендера: {renderer_type}',
        }

    def render_work_error_payload(self, error):
        return {
            'success': False,
            'error': str(error),
        }

    def render_status_payload(self):
        return {
            'status': 'ready',
            'message': 'Система готова к рендерингу',
        }

    def remedial_sheet_error_payload(self, message):
        return {
            'status': 'error',
            'message': message,
        }

    def remedial_sheet_batch_error_payload(self, message):
        return {
            'success': False,
            'error': message,
        }

    def work_specs_from_formset(self, formset):
        specs = []
        for row in formset.cleaned_data:
            if not row or row.get('DELETE'):
                continue

            analog_group = row.get('analog_group')
            if not analog_group:
                continue

            specs.append(
                WorkTaskSelectionParams(
                    analog_group_id=str(analog_group.pk),
                    order=row.get('order') or 0,
                    count=row.get('count') or 1,
                    weight=row.get('weight') or 1,
                    bank_role_filter=(
                        row.get('bank_role_filter') or TASK_BANK_ROLE_ANY
                    ),
                    render_mode=(
                        row.get('render_mode') or TASK_RENDER_MODE_TASK_ONLY
                    ),
                    is_assessable=row.get('is_assessable', True),
                    blank_cells_after=row.get('blank_cells_after', False),
                    blank_cells_rows=(
                        row.get('blank_cells_rows') or DEFAULT_BLANK_CELLS_ROWS
                    ),
                )
            )
        return specs

    def work_content_blocks_from_formset(self, formset):
        content_blocks = []
        for row in formset.cleaned_data:
            if not row or row.get('DELETE'):
                continue

            content_type = row.get('content_type')
            if not content_type:
                continue

            is_theory = content_type == 'theory'
            content_blocks.append(
                WorkContentBlockParams(
                    content_type=content_type,
                    order=row.get('order') or 0,
                    title=(row.get('title') or '').strip(),
                    body=(
                        ''
                        if is_theory
                        else (row.get('body') or '').strip()
                    ),
                    topic_ids=[
                        str(topic.pk)
                        for topic in row.get('topics') or ()
                    ] if is_theory else [],
                    include_subtopics=(
                        row.get('include_subtopics', False)
                        if is_theory
                        else False
                    ),
                )
            )
        return content_blocks

    def compose_variants_request_from_form(self, form, work_id):
        return ComposeWorkVariantsRequest(
            work_id=work_id,
            count=form.cleaned_data['count'],
        )

    def render_work_document_request_from_post(self, post_data, work_id):
        return RenderWorkDocumentRequest(
            work_id=work_id,
            options=build_work_render_options(post_data),
            presentation_profile_id=self._presentation_profile_id_from_post(post_data),
            variant_id=self._variant_id_from_post(post_data),
        )

    def document_renderer_type_from_post(self, post_data, default='pdf'):
        return renderer_type_from_data(post_data, default=default)

    def render_remedial_sheet_request_from_post(self, post_data, variant_id):
        return RenderRemedialSheetDocumentRequest(
            variant_id=variant_id,
            options=build_remedial_sheet_render_options(post_data),
            presentation_profile_id=self._presentation_profile_id_from_post(post_data),
        )

    def render_remedial_sheet_batch_request_from_post(self, post_data, work_id):
        return RenderRemedialSheetBatchDocumentRequest(
            work_id=work_id,
            options=build_remedial_sheet_render_options(post_data),
            presentation_profile_id=self._presentation_profile_id_from_post(post_data),
        )

    def _presentation_profile_id_from_post(self, post_data):
        return post_data.get('presentation_profile_id', '').strip()

    def _variant_id_from_post(self, post_data):
        variant_id = post_data.get('variant_selection', '').strip()
        return '' if variant_id == 'all' else variant_id

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

    def remedial_sheet_batch_response_payload(self, result):
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
                f'Пакет листов работы над ошибками создан '
                f'({result.renderer_type.upper()})'
            ),
            'files': files_info,
            'total_files': len(files_info),
        }
