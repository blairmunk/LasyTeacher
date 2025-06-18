from django.db.models import Q

def search_by_uuid(model_class, query):
    """Универсальная функция поиска по UUID"""
    if not query:
        return model_class.objects.none()
    
    # Убираем символ # если есть
    clean_query = query.replace('#', '').strip()
    
    if not clean_query:
        return model_class.objects.none()
    
    # Поиск по частичному UUID (от 3 символов)
    if len(clean_query) >= 3:
        return model_class.objects.filter(
            Q(uuid__iendswith=clean_query.lower()) | 
            Q(uuid__icontains=clean_query.lower())
        ).distinct()
    
    return model_class.objects.none()

def get_object_by_short_uuid(model_class, short_uuid):
    """Получить объект по короткому UUID"""
    clean_uuid = short_uuid.replace('#', '').strip().lower()
    
    if len(clean_uuid) < 3:
        return None
        
    matches = model_class.objects.filter(uuid__iendswith=clean_uuid)
    
    if matches.count() == 1:
        return matches.first()
    elif matches.count() > 1:
        # Если несколько совпадений, вернуть точное совпадение
        for obj in matches:
            if str(obj.uuid)[-len(clean_uuid):].lower() == clean_uuid:
                return obj
    
    return None
