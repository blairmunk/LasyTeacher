from django.db.models import Q


def search_by_uuid(model_class, query, related_uuid_fields=None):
    """Поиск по UUID — Python-side фильтр.
    
    related_uuid_fields: список FK-полей для поиска по связанным UUID.
    Пример: ['topic', 'subtopic'] — ищет и в topic.id, и в subtopic.id
    """
    clean = query.replace('#', '').replace('-', '').replace(' ', '').strip().lower()

    if len(clean) < 3:
        return model_class.objects.none()

    matching_ids = set()

    # Поиск по собственному UUID
    for obj_id in model_class.objects.values_list('id', flat=True).iterator():
        id_clean = str(obj_id).replace('-', '').lower()
        if clean in id_clean:
            matching_ids.add(obj_id)

    # Поиск по UUID связанных моделей
    if related_uuid_fields:
        for field in related_uuid_fields:
            fk_field = f'{field}_id'
            try:
                for obj_id, fk_id in model_class.objects.values_list('id', fk_field).iterator():
                    if fk_id:
                        fk_clean = str(fk_id).replace('-', '').lower()
                        if clean in fk_clean:
                            matching_ids.add(obj_id)
            except Exception:
                pass  # Поле не существует — пропускаем

    if not matching_ids:
        return model_class.objects.none()

    return model_class.objects.filter(id__in=matching_ids)


def get_object_by_short_uuid(model_class, short_uuid):
    """Получить объект по короткому UUID (последние N символов)"""
    clean = short_uuid.replace('#', '').replace('-', '').strip().lower()

    if len(clean) < 3:
        return None

    results = search_by_uuid(model_class, clean)

    if results.count() == 1:
        return results.first()
    elif results.count() > 1:
        for obj in results:
            id_str = str(obj.id).replace('-', '').lower()
            if id_str.endswith(clean):
                return obj
        return results.first()

    return None


def pluralize_results(count):
    """Правильное склонение: 1 результат, 2 результата, 5 результатов"""
    if 11 <= count % 100 <= 19:
        return f'{count} результатов'
    last = count % 10
    if last == 1:
        return f'{count} результат'
    elif 2 <= last <= 4:
        return f'{count} результата'
    return f'{count} результатов'
