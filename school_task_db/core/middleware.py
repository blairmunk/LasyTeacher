from core_logic.use_cases.resolve_academic_year import (
    ResolveAcademicYearRequest,
)
from infrastructure.container import container


class AcademicYearMiddleware:
    """Добавляет текущий учебный год в request и context"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        selection = container.resolve_academic_year_use_case().execute(
            ResolveAcademicYearRequest(
                requested_year_id=request.GET.get('year', ''),
                stored_year_id=request.session.get('academic_year_id', ''),
            )
        )
        request.current_year = selection.current_year
        if selection.year_id:
            if request.session.get('academic_year_id') != selection.year_id:
                request.session['academic_year_id'] = selection.year_id
        else:
            request.session.pop('academic_year_id', None)
        return self.get_response(request)
