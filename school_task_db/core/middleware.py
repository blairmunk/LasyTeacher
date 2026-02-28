from core.models import AcademicYear


class AcademicYearMiddleware:
    """Добавляет текущий учебный год в request и context"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пользователь может переключить год через GET или session
        year_id = request.GET.get('year')

        if year_id:
            try:
                year = AcademicYear.objects.get(pk=year_id)
                request.session['academic_year_id'] = str(year.pk)
            except (AcademicYear.DoesNotExist, ValueError):
                year = AcademicYear.get_current()
        else:
            stored_id = request.session.get('academic_year_id')
            if stored_id:
                try:
                    year = AcademicYear.objects.get(pk=stored_id)
                except AcademicYear.DoesNotExist:
                    year = AcademicYear.get_current()
            else:
                year = AcademicYear.get_current()

        request.current_year = year
        return self.get_response(request)
