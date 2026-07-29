from infrastructure.container import container


def academic_year(request):
    """Добавляет учебный год во все шаблоны"""
    years = container.get_academic_year_list_use_case().execute()
    return {
        'current_year': getattr(request, 'current_year', None),
        'all_years': years.academic_years,
    }
