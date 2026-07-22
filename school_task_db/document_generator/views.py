from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from infrastructure.container import container
from infrastructure.forms.document_template_django_forms import (
    DocumentTemplateForm,
)
from core_logic.use_cases.get_document_template_form_data import (
    GetDocumentTemplateFormDataRequest,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE


class DocumentTemplateEditorView(TemplateView):
    template_name = 'document_generator/template_editor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adapter = container.document_template_form_adapter
        request = adapter.editor_data_request_from_query(self.request.GET)
        editor_data = (
            container
            .get_document_template_editor_data_use_case()
            .execute(request)
        )
        context.update(adapter.editor_context(editor_data, request))
        return context


class DocumentTemplateCreateView(TemplateView):
    template_name = 'document_generator/template_form.html'
    page_title = 'Новый шаблон документа'

    def get_context_data(self, **kwargs):
        form_data = kwargs.pop('form_data', None) or self._form_data()
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form') or self._form(
            form_data=form_data,
            initial={
                'template_type': self.request.GET.get(
                    'type',
                    WORK_DOCUMENT_TYPE,
                ),
            },
        )
        context.update(
            container.document_template_form_adapter.create_context(
                form=form,
                document_types=form_data.document_types,
                sections=form_data.sections,
            )
        )
        context['page_title'] = self.page_title
        context['submit_label'] = 'Сохранить'
        return context

    def post(self, request, *args, **kwargs):
        form_data = self._form_data()
        form = self._form(data=request.POST, form_data=form_data)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        result = container.create_document_template_use_case().execute(
            container.document_template_form_adapter.create_params_from_form(
                form,
            )
        )
        if not result.success:
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        messages.success(request, 'Шаблон документа создан.')
        return redirect('document_generator:template-editor')

    def _form(self, *args, form_data=None, **kwargs):
        form_data = form_data or self._form_data()
        return DocumentTemplateForm(
            *args,
            document_types=form_data.document_types,
            sections=form_data.sections,
            **kwargs,
        )

    def _form_data(self, template_id=''):
        return (
            container
            .get_document_template_form_data_use_case()
            .execute(
                GetDocumentTemplateFormDataRequest(
                    template_id=template_id,
                    renderable_only=True,
                ),
            )
        )


class DocumentTemplateUpdateView(DocumentTemplateCreateView):
    page_title = 'Редактирование шаблона'

    def _form_data(self, template_id=''):
        form_data = super()._form_data(template_id or str(self.kwargs['pk']))
        if form_data.template is None:
            raise Http404('Шаблон документа не найден')
        return form_data

    def get_context_data(self, **kwargs):
        form_data = kwargs.pop('form_data', None) or self._form_data()
        template = form_data.template
        form = kwargs.get('form') or self._form(
            form_data=form_data,
            initial=(
                container
                .document_template_form_adapter
                .form_initial_from_template(template)
            ),
        )
        context = super().get_context_data(
            form=form,
            form_data=form_data,
            **kwargs,
        )
        context['template'] = template
        context['page_title'] = self.page_title
        context['submit_label'] = 'Сохранить изменения'
        return context

    def post(self, request, *args, **kwargs):
        form_data = self._form_data()
        form = self._form(data=request.POST, form_data=form_data)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        result = container.update_document_template_use_case().execute(
            container.document_template_form_adapter.update_params_from_form(
                form,
                template_id=str(self.kwargs['pk']),
            )
        )
        if not result.success:
            if result.status == 'not_found':
                raise Http404('Шаблон документа не найден')
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        messages.success(request, 'Шаблон документа обновлён.')
        return redirect('document_generator:template-editor')
