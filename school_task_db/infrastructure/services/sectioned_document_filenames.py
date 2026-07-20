"""Filename builders for sectioned document renderers."""


def work_html_filename(request):
    return _source_filename(request, prefix='work', extension='html')


def remedial_html_filename(request):
    return _source_filename(request, prefix='remedial', extension='html')


def work_latex_filename(request):
    return _source_filename(request, prefix='work', extension='tex')


def remedial_latex_filename(request):
    return _source_filename(request, prefix='remedial', extension='tex')


def _source_filename(request, prefix, extension):
    if request.document.source and request.document.source.source_id:
        return f'{prefix}_{request.document.source.source_id}.{extension}'
    return f'{prefix}.{extension}'
