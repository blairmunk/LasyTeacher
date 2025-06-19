from .models import ReferenceManager

# Предметы
def get_subject_choices(include_empty=False):
    return ReferenceManager.get_choices('subjects', include_empty)

# Типы заданий
def get_task_type_choices(include_empty=False):
    return ReferenceManager.get_choices('task_types', include_empty)

# Уровни сложности (числовые)
def get_difficulty_choices(include_empty=False):
    return ReferenceManager.get_numeric_choices('difficulty_levels', include_empty)

# Когнитивные уровни
def get_cognitive_level_choices(include_empty=False):
    return ReferenceManager.get_choices('cognitive_levels', include_empty)

# Типы работ
def get_work_type_choices(include_empty=False):
    return ReferenceManager.get_choices('work_types', include_empty)

# Классы (числовые)
def get_grade_level_choices(include_empty=False):
    return ReferenceManager.get_numeric_choices('grade_levels', include_empty)

# Типовые комментарии
def get_comment_category_choices(include_empty=False):
    return ReferenceManager.get_choices('comment_categories', include_empty)

# Дополнительные утилиты
def get_subject_name(code):
    item = ReferenceManager.get_item('subjects', code)
    return item.name if item else code

def get_task_type_name(code):
    item = ReferenceManager.get_item('task_types', code)
    return item.name if item else code

def get_difficulty_name(numeric_value):
    try:
        from .models import ReferenceItem
        item = ReferenceItem.objects.get(
            category__code='difficulty_levels',
            numeric_value=numeric_value,
            is_active=True
        )
        return item.name
    except ReferenceItem.DoesNotExist:
        return f"Уровень {numeric_value}"

# Функция для динамического обновления choices в формах
def refresh_model_choices():
    """Обновляет choices во всех моделях после изменения справочников"""
    from django.apps import apps
    
    # Получаем все модели, которые используют справочники
    models_to_update = [
        apps.get_model('tasks', 'Task'),
        apps.get_model('curriculum', 'Topic'),
        apps.get_model('works', 'Work'),
        # Добавляем другие модели по мере необходимости
    ]
    
    for model in models_to_update:
        # Обновляем choices в полях модели
        for field in model._meta.fields:
            if hasattr(field, 'choices') and field.choices:
                # Определяем тип справочника по имени поля
                if 'subject' in field.name:
                    field.choices = get_subject_choices()
                elif 'task_type' in field.name:
                    field.choices = get_task_type_choices()
                elif 'difficulty' in field.name:
                    field.choices = get_difficulty_choices()
                # и т.д.
