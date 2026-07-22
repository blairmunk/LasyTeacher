from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from infrastructure.container import container
from infrastructure.forms.document_template_django_forms import (
    DocumentTemplateForm,
)
from core_logic.use_cases.get_document_section_catalog import (
    GetDocumentSectionCatalogRequest,
)
from core_logic.use_cases.get_document_type_catalog import (
    GetDocumentTypeCatalogRequest,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE
from core_logic.use_cases.get_document_template import GetDocumentTemplateRequest


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
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form') or self._form(
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
                document_types=self._document_types(),
                sections=self._sections(),
            )
        )
        context['page_title'] = self.page_title
        context['submit_label'] = 'Сохранить'
        return context

    def post(self, request, *args, **kwargs):
        form = self._form(data=request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        result = container.create_document_template_use_case().execute(
            container.document_template_form_adapter.create_params_from_form(
                form,
            )
        )
        if not result.success:
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(self.get_context_data(form=form))

        messages.success(request, 'Шаблон документа создан.')
        return redirect('document_generator:template-editor')

    def _form(self, *args, **kwargs):
        return DocumentTemplateForm(
            *args,
            document_types=self._document_types(),
            sections=self._sections(),
            **kwargs,
        )

    def _document_types(self):
        return (
            container
            .get_document_type_catalog_use_case()
            .execute(GetDocumentTypeCatalogRequest(renderable_only=True))
            .document_types
        )

    def _sections(self):
        return (
            container
            .get_document_section_catalog_use_case()
            .execute(GetDocumentSectionCatalogRequest(renderable_only=True))
            .sections
        )


class DocumentTemplateUpdateView(DocumentTemplateCreateView):
    page_title = 'Редактирование шаблона'

    def _template(self):
        data = container.get_document_template_use_case().execute(
            GetDocumentTemplateRequest(template_id=str(self.kwargs['pk']))
        )
        if data.template is None:
            raise Http404('Шаблон документа не найден')
        return data.template

    def get_context_data(self, **kwargs):
        template = self._template()
        form = kwargs.get('form') or self._form(
            initial=(
                container
                .document_template_form_adapter
                .form_initial_from_template(template)
            ),
        )
        context = super().get_context_data(form=form, **kwargs)
        context['template'] = template
        context['page_title'] = self.page_title
        context['submit_label'] = 'Сохранить изменения'
        return context

    def post(self, request, *args, **kwargs):
        self._template()
        form = self._form(data=request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

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
            return self.render_to_response(self.get_context_data(form=form))

        messages.success(request, 'Шаблон документа обновлён.')
        return redirect('document_generator:template-editor')
