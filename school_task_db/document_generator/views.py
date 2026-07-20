from django.views.generic import TemplateView

from infrastructure.container import container


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
