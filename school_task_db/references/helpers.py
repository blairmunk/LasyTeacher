def get_reference_choices(category, include_empty=False):
    """
    Получить choices из справочника
    ВАЖНО: импорт модели ТОЛЬКО внутри функции!
    """
    try:
        # Импорт только внутри функции - избегаем циклических импортов
        from .models import SimpleReference
        
        ref = SimpleReference.objects.get(category=category, is_active=True)
        
        if include_empty:
            return ref.get_choices_with_empty()
        else:
            return ref.get_choices()
    
    except:
        # Если справочник не найден - используем fallback
        fallback = get_fallback_choices(category)
        if include_empty and fallback:
            return [('', '--- Выберите ---')] + fallback
        return fallback

def get_subject_reference_choices(subject, category, include_empty=False):
    """
    Получить choices из справочника кодификатора
    """
    try:
        # Импорт только внутри функции
        from .models import SubjectReference
        
        ref = SubjectReference.objects.get(
            subject=subject, 
            category=category, 
            is_active=True
        )
        
        if include_empty:
            return ref.get_choices_with_empty()
        else:
            return ref.get_choices()
    
    except:
        if include_empty:
            return [('', '--- Выберите ---')]
        return []

def get_fallback_choices(category):
    """
    Базовые choices если справочник недоступен
    НЕ импортируем ничего - только статические данные!
    """
    fallbacks = {
        'task_types': [
            ('computational', 'Расчётная задача'),
            ('qualitative', 'Качественная задача'),
            ('theoretical', 'Теоретический вопрос'),
            ('practical', 'Практическое задание'),
            ('test', 'Тестовое задание'),
        ],
        'difficulty_levels': [
            ('basic', 'Базовый'),
            ('advanced', 'Повышенный'),
            ('high', 'Высокий'),
        ],
        'cognitive_levels': [
            ('remember', 'Запоминание'),
            ('understand', 'Понимание'),
            ('apply', 'Применение'),
            ('analyze', 'Анализ'),
        ],
        'work_types': [
            ('test', 'Контрольная работа'),
            ('quiz', 'Самостоятельная работа'),
            ('exam', 'Экзамен'),
        ],
        'subjects': [
            ('mathematics', 'Математика'),
            ('algebra', 'Алгебра'),
            ('geometry', 'Геометрия'),
            ('physics', 'Физика'),
        ],
        'comment_categories': [
            ('excellent', 'Отлично'),
            ('good', 'Хорошо'),
            ('needs_improvement', 'Требует улучшения'),
        ]
    }
    return fallbacks.get(category, [])

# Удобные функции для каждого типа справочника
def get_task_type_choices(include_empty=False):
    """Получить типы заданий"""
    return get_reference_choices('task_types', include_empty)

def get_difficulty_choices(include_empty=False):
    """Получить уровни сложности"""
    return get_reference_choices('difficulty_levels', include_empty)

def get_difficulty_choices_for_forms(include_empty=False):
    """Получить choices сложности для форм (всегда numbers + labels)"""
    from tasks.models import Task
    
    try:
        # Пытаемся получить из справочника
        ref_choices = get_reference_choices('difficulty_levels', include_empty=False)
        
        if ref_choices:
            # Проверяем, что в справочнике числа
            numbers = []
            for code, name in ref_choices:
                try:
                    numbers.append(int(code))
                except ValueError:
                    # Если не числа - используем статические
                    return Task.DIFFICULTY_LEVELS if not include_empty else [('', '--- Выберите ---')] + Task.DIFFICULTY_LEVELS
            
            # Создаем choices: число -> название из модели
            choices = []
            for num in sorted(numbers):
                # Ищем название в статических choices модели
                for choice_num, choice_name in Task.DIFFICULTY_LEVELS:
                    if choice_num == num:
                        choices.append((num, choice_name))
                        break
            
            if include_empty:
                choices = [('', '--- Выберите ---')] + choices
            
            return choices
    except:
        pass
    
    # Fallback на статические choices из модели
    choices = Task.DIFFICULTY_LEVELS
    if include_empty:
        choices = [('', '--- Выберите ---')] + choices
    return choices

def get_cognitive_level_choices(include_empty=False):
    """Получить когнитивные уровни"""
    return get_reference_choices('cognitive_levels', include_empty)

def get_work_type_choices(include_empty=False):
    """Получить типы работ"""
    return get_reference_choices('work_types', include_empty)

def get_subject_choices(include_empty=False):
    """Получить предметы"""
    return get_reference_choices('subjects', include_empty)

def get_comment_category_choices(include_empty=False):
    """Получить категории комментариев"""
    return get_reference_choices('comment_categories', include_empty)

# Справочники кодификатора
def get_content_elements_for_subject(subject, include_empty=False):
    """Получить элементы содержания для предмета"""
    return get_subject_reference_choices(subject, 'content_elements', include_empty)

def get_requirement_elements_for_subject(subject, include_empty=False):
    """Получить элементы требований для предмета"""
    return get_subject_reference_choices(subject, 'requirement_elements', include_empty)
