from infrastructure.container import container
from infrastructure.services.frontend_asset_urls import frontend_asset_urls


def academic_year(request):
    """Добавляет учебный год во все шаблоны"""
    years = container.get_academic_year_list_use_case().execute()
    return {
        'current_year': getattr(request, 'current_year', None),
        'all_years': years.academic_years,
    }


def frontend_assets(request):
    """Expose deployment-selected browser assets to all UI templates."""
    return {'frontend_assets': frontend_asset_urls()}
