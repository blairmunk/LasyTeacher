from core.models import AcademicYear


def academic_year(request):
    """Добавляет учебный год во все шаблоны"""
    return {
        'current_year': getattr(request, 'current_year', None),
        'all_years': AcademicYear.objects.all().order_by('-start_date'),
    }
