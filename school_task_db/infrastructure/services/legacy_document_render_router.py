"""Route legacy document render requests to file renderers."""


class LegacyDocumentRenderRouter:
    def __init__(self, legacy_file_renderer, file_store):
        self.legacy_file_renderer = legacy_file_renderer
        self.file_store = file_store

    def render_work(self, work, options):
        render_target = options.render_target
        renderer_type = render_target.renderer_type
        content_config = options.content_config

        if renderer_type == 'latex':
            return self.file_store.document_from_paths(
                file_type='latex',
                file_paths=self.legacy_file_renderer.render_latex_work(
                    work,
                    content_config,
                    render_target.page_format,
                ),
            )
        if renderer_type == 'html':
            return self.file_store.document_from_paths(
                file_type='html',
                file_paths=self.legacy_file_renderer.render_html_work(
                    work,
                    content_config,
                ),
            )
        return self.file_store.document_from_paths(
            file_type='pdf',
            file_paths=self.legacy_file_renderer.render_pdf_work(
                work,
                content_config,
                render_target.page_format,
            ),
        )

    def render_remedial_sheet(self, variant, options):
        render_target = options.render_target
        renderer_type = render_target.renderer_type
        content_config = options.content_config

        if renderer_type == 'latex':
            return self.file_store.document_from_paths(
                file_type='latex',
                file_paths=self.legacy_file_renderer.render_remedial_latex(
                    variant,
                    content_config,
                    render_target.page_format,
                ),
            )
        if renderer_type == 'html':
            return self.file_store.document_from_paths(
                file_type='html',
                file_paths=self.legacy_file_renderer.render_remedial_html(
                    variant,
                    content_config,
                ),
            )
        return self.file_store.document_from_paths(
            file_type='pdf',
            file_paths=self.legacy_file_renderer.render_remedial_pdf(
                variant,
                content_config,
                render_target.page_format,
            ),
        )
