from django.core.management.base import BaseCommand
from django.db import transaction
from references.models import SimpleReference, SubjectReference

class Command(BaseCommand):
    help = 'Инициализация простых справочников начальными данными'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать существующие справочники'
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        with transaction.atomic():
            self.stdout.write(self.style.SUCCESS('🚀 Инициализация простых справочников...'))
            
            created_count = 0
            created_count += self.create_simple_references(force)
            created_count += self.create_subject_references(force)

        self.stdout.write(
            self.style.SUCCESS(f'✅ Готово! Создано {created_count} справочников.')
        )

    def create_simple_references(self, force=False):
        """Создание простых справочников"""
        self.stdout.write('  📝 Создание простых справочников...')
        
        references_data = [
            # Типы заданий
            ('task_types', '''Расчётная задача
Качественная задача
Теоретический вопрос
Практическое задание
Тестовое задание
Творческое задание
Исследовательское задание
Экспериментальное задание'''),
            
            # Уровни сложности
            ('difficulty_levels', '''Подготовительный
Базовый
Повышенный
Высокий
Экспертный'''),
            
            # Когнитивные уровни (по Блуму)
            ('cognitive_levels', '''Запоминание
Понимание
Применение
Анализ
Оценка
Создание'''),
            
            # Типы работ
            ('work_types', '''Контрольная работа
Самостоятельная работа
Экзамен
Диагностическая работа
Домашняя работа
Практическая работа
Лабораторная работа
Проектная работа
Зачёт
Олимпиада'''),
            
            # Предметы
            ('subjects', '''Математика
Алгебра
Геометрия
Физика
Химия
Русский язык
Литература
История
Обществознание
Биология
География
Английский язык
Немецкий язык
Французский язык
Информатика
Технология
Физическая культура
ОБЖ
Астрономия'''),
            
            # Категории комментариев
            ('comment_categories', '''Отличная работа
Хорошая работа
Удовлетворительно
Требует улучшения
Типичная ошибка
Рекомендация
Похвала
Замечание
Внимание к деталям
Творческий подход'''),
        ]
        
        created_count = 0
        
        for category, items_text in references_data:
            if force:
                # Удаляем существующий при --force
                SimpleReference.objects.filter(category=category).delete()
            
            obj, created = SimpleReference.objects.get_or_create(
                category=category,
                defaults={
                    'items_text': items_text,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                items_count = len(obj.get_items_list())
                self.stdout.write(f'    ✅ {obj.get_category_display()}: {items_count} элементов')
            elif force:
                # Обновляем содержимое при --force
                obj.items_text = items_text
                obj.save()
                items_count = len(obj.get_items_list())
                self.stdout.write(f'    🔄 {obj.get_category_display()}: обновлено, {items_count} элементов')
            else:
                self.stdout.write(f'    ⚠️  {obj.get_category_display()}: уже существует')
        
        return created_count

    def create_subject_references(self, force=False):
        """Создание справочников кодификатора по предметам"""
        self.stdout.write('  📚 Создание справочников кодификатора...')
        
        # Элементы содержания для математики
        math_content = '''1.1|Натуральные числа
1.2|Дроби
1.3|Рациональные числа
1.4|Действительные числа
1.5|Измерения, приближения, оценки
2.1|Буквенные выражения
2.2|Многочлены
2.3|Алгебраические дроби
2.4|Степень с целым показателем
3.1|Уравнения
3.2|Неравенства
3.3|Системы уравнений
3.4|Системы неравенств
4.1|Понятие последовательности
4.2|Арифметическая прогрессия
4.3|Геометрическая прогрессия
5.1|Понятие функции
5.2|Свойства функций
5.3|Линейная функция
5.4|Квадратичная функция
5.5|Степенная функция'''

        # Элементы требований для математики
        math_requirements = '''1.1|Понятие математического доказательства
1.2|Понятие алгоритма
1.3|Математические формулы и модели
2.1|Выполнение вычислений и преобразований
2.2|Выполнение алгебраических преобразований
2.3|Решение уравнений и неравенств
2.4|Построение и исследование функций
2.5|Выполнение действий с геометрическими фигурами
2.6|Проведение доказательств
3.1|Анализ реальных числовых данных
3.2|Решение практических задач
3.3|Интерпретация результатов'''

        # Элементы содержания для физики
        physics_content = '''1.1|Механическое движение
1.2|Взаимодействие тел
1.3|Законы сохранения
1.4|Механические колебания и волны
2.1|Тепловые явления
2.2|Изменения агрегатных состояний
2.3|Тепловые двигатели
3.1|Электризация тел
3.2|Постоянный ток
3.3|Магнитные явления
3.4|Электромагнитная индукция
3.5|Электромагнитные колебания и волны
4.1|Радиоактивность
4.2|Строение атома
4.3|Ядерные реакции'''

        subject_references_data = [
            # Математика
            ('mathematics', 'content_elements', math_content),
            ('mathematics', 'requirement_elements', math_requirements),
            
            # Физика  
            ('physics', 'content_elements', physics_content),
            ('physics', 'requirement_elements', '''1.1|Понимание смысла физических понятий
1.2|Понимание смысла физических законов
1.3|Понимание принципов действия приборов
2.1|Описание и объяснение физических явлений
2.2|Представление результатов измерений
2.3|Решение задач на применение законов
2.4|Проведение простых физических опытов'''),
            
            # Алгебра (упрощенный вариант)
            ('algebra', 'content_elements', '''1.1|Числа и вычисления
2.1|Алгебраические выражения
2.2|Многочлены и их разложение
3.1|Уравнения и их системы
3.2|Неравенства и их системы
4.1|Числовые последовательности
5.1|Функции и их свойства'''),
            
            # Геометрия
            ('geometry', 'content_elements', '''6.1|Начальные понятия геометрии
6.2|Треугольник
6.3|Четырёхугольники
6.4|Многоугольники
6.5|Окружность и круг
6.6|Измерение геометрических величин
7.1|Координаты и векторы
8.1|Тела и поверхности в пространстве'''),
        ]
        
        created_count = 0
        
        for subject, category, items_text in subject_references_data:
            if force:
                SubjectReference.objects.filter(subject=subject, category=category).delete()
            
            obj, created = SubjectReference.objects.get_or_create(
                subject=subject,
                category=category,
                defaults={
                    'items_text': items_text,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                items_count = len(obj.get_items_dict())
                self.stdout.write(f'    ✅ {obj.get_subject_display()} - {obj.get_category_display()}: {items_count} элементов')
            elif force:
                obj.items_text = items_text
                obj.save()
                items_count = len(obj.get_items_dict())
                self.stdout.write(f'    🔄 {obj.get_subject_display()} - {obj.get_category_display()}: обновлено')
            else:
                self.stdout.write(f'    ⚠️  {obj.get_subject_display()} - {obj.get_category_display()}: уже существует')
        
        return created_count
