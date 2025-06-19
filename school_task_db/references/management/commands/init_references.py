from django.core.management.base import BaseCommand
from django.db import transaction
from references.models import ReferenceCategory, ReferenceItem

class Command(BaseCommand):
    help = 'Инициализация справочников начальными данными'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать существующие данные'
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        with transaction.atomic():
            self.stdout.write('Инициализация справочников...')
            
            # 1. Предметы
            self.create_subjects(force)
            
            # 2. Типы заданий
            self.create_task_types(force)
            
            # 3. Уровни сложности
            self.create_difficulty_levels(force)
            
            # 4. Когнитивные уровни
            self.create_cognitive_levels(force)
            
            # 5. Типы работ
            self.create_work_types(force)
            
            # 6. Классы
            self.create_grade_levels(force)
            
            # 7. Категории комментариев
            self.create_comment_categories(force)

        self.stdout.write(
            self.style.SUCCESS('✅ Справочники успешно инициализированы!')
        )

    def create_subjects(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='subjects',
            defaults={
                'name': 'Предметы',
                'description': 'Учебные предметы и дисциплины',
                'is_system': False
            }
        )
        
        if created or force:
            self.stdout.write('  📚 Создание предметов...')
            
            subjects_data = [
                ('mathematics', 'Математика', '#2E86AB', 'fas fa-calculator'),
                ('algebra', 'Алгебра', '#A23B72', 'fas fa-square-root-alt'),
                ('geometry', 'Геометрия', '#F18F01', 'fas fa-shapes'),
                ('physics', 'Физика', '#C73E1D', 'fas fa-atom'),
                ('chemistry', 'Химия', '#4CAF50', 'fas fa-flask'),
                ('russian', 'Русский язык', '#9C27B0', 'fas fa-language'),
                ('literature', 'Литература', '#795548', 'fas fa-book-open'),
                ('history', 'История', '#FF9800', 'fas fa-landmark'),
                ('biology', 'Биология', '#4CAF50', 'fas fa-dna'),
                ('geography', 'География', '#009688', 'fas fa-globe'),
                ('english', 'Английский язык', '#3F51B5', 'fas fa-globe-americas'),
                ('informatics', 'Информатика', '#607D8B', 'fas fa-laptop-code'),
            ]
            
            for i, (code, name, color, icon) in enumerate(subjects_data, 1):
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        'name': name,
                        'order': i * 10,
                        'color': color,
                        'icon': icon,
                        'is_active': True
                    }
                )

    def create_task_types(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='task_types',
            defaults={
                'name': 'Типы заданий',
                'description': 'Типы учебных заданий и упражнений'
            }
        )
        
        if created or force:
            self.stdout.write('  📝 Создание типов заданий...')
            
            task_types_data = [
                ('computational', 'Расчётная задача', '#2196F3', 'fas fa-calculator'),
                ('qualitative', 'Качественная задача', '#FF9800', 'fas fa-lightbulb'),
                ('theoretical', 'Теоретический вопрос', '#9C27B0', 'fas fa-question-circle'),
                ('practical', 'Практическое задание', '#4CAF50', 'fas fa-tools'),
                ('test', 'Тестовое задание', '#F44336', 'fas fa-check-square'),
                ('creative', 'Творческое задание', '#E91E63', 'fas fa-palette'),
                ('research', 'Исследовательское задание', '#795548', 'fas fa-search'),
            ]
            
            for i, (code, name, color, icon) in enumerate(task_types_data, 1):
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        'name': name,
                        'order': i * 10,
                        'color': color,
                        'icon': icon,
                        'is_active': True
                    }
                )

    def create_difficulty_levels(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='difficulty_levels',
            defaults={
                'name': 'Уровни сложности',
                'description': 'Уровни сложности заданий'
            }
        )
        
        if created or force:
            self.stdout.write('  ⭐ Создание уровней сложности...')
            
            difficulty_data = [
                ('preparatory', 'Подготовительный', 1, '#4CAF50', 'far fa-star'),
                ('basic', 'Базовый', 2, '#8BC34A', 'fas fa-star'),
                ('advanced', 'Повышенный', 3, '#FF9800', 'fas fa-star'),
                ('high', 'Высокий', 4, '#FF5722', 'fas fa-star'),
                ('expert', 'Экспертный', 5, '#F44336', 'fas fa-star'),
            ]
            
            for code, name, value, color, icon in difficulty_data:
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        'name': name,
                        'numeric_value': value,
                        'order': value * 10,
                        'color': color,
                        'icon': icon,
                        'is_active': True
                    }
                )

    def create_cognitive_levels(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='cognitive_levels',
            defaults={
                'name': 'Когнитивные уровни',
                'description': 'Уровни познавательной деятельности (по Блуму)'
            }
        )
        
        if created or force:
            self.stdout.write('  🧠 Создание когнитивных уровней...')
            
            cognitive_data = [
                ('remember', 'Запоминание', '#9E9E9E', 'fas fa-brain'),
                ('understand', 'Понимание', '#2196F3', 'fas fa-lightbulb'),
                ('apply', 'Применение', '#4CAF50', 'fas fa-tools'),
                ('analyze', 'Анализ', '#FF9800', 'fas fa-search'),
                ('evaluate', 'Оценка', '#9C27B0', 'fas fa-balance-scale'),
                ('create', 'Создание', '#F44336', 'fas fa-magic'),
            ]
            
            for i, (code, name, color, icon) in enumerate(cognitive_data, 1):
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        'name': name,
                        'order': i * 10,
                        'color': color,
                        'icon': icon,
                        'is_active': True
                    }
                )

    def create_work_types(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='work_types',
            defaults={
                'name': 'Типы работ',
                'description': 'Типы контрольных и проверочных работ'
            }
        )
        
        if created or force:
            self.stdout.write('  📋 Создание типов работ...')
            
            work_types_data = [
                ('test', 'Контрольная работа', '#F44336', 'fas fa-file-alt'),
                ('quiz', 'Самостоятельная работа', '#2196F3', 'fas fa-edit'),
                ('exam', 'Экзамен', '#9C27B0', 'fas fa-graduation-cap'),
                ('diagnostic', 'Диагностическая работа', '#FF9800', 'fas fa-stethoscope'),
                ('homework', 'Домашняя работа', '#4CAF50', 'fas fa-home'),
                ('practice', 'Практическая работа', '#795548', 'fas fa-tools'),
                ('project', 'Проектная работа', '#E91E63', 'fas fa-project-diagram'),
            ]
            
            for i, (code, name, color, icon) in enumerate(work_types_data, 1):
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        'name': name,
                        'order': i * 10,
                        'color': color,
                        'icon': icon,
                        'is_active': True
                    }
                )

    def create_grade_levels(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='grade_levels',
            defaults={
                'name': 'Классы',
                'description': 'Уровни обучения (классы)'
            }
        )
        
        if created or force:
            self.stdout.write('  🎓 Создание классов...')
            
            for grade in range(1, 12):  # 1-11 классы
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=f'grade_{grade}',
                    defaults={
                        'name': f'{grade} класс',
                        'numeric_value': grade,
                        'order': grade * 10,
                        'is_active': True
                    }
                )

    def create_comment_categories(self, force=False):
        category, created = ReferenceCategory.objects.get_or_create(
            code='comment_categories',
            defaults={
                'name': 'Категории комментариев',
                'description': 'Категории типовых комментариев для проверки работ'
            }
        )
        
        if created or force:
            self.stdout.write('  💬 Создание категорий комментариев...')
            
            comment_categories_data = [
                ('excellent', 'Отличная работа', '#4CAF50', 'fas fa-star'),
                ('good', 'Хорошая работа', '#2196F3', 'fas fa-thumbs-up'),
                ('satisfactory', 'Удовлетворительно', '#FF9800', 'fas fa-hand-paper'),
                ('needs_improvement', 'Требует улучшения', '#FF5722', 'fas fa-exclamation-triangle'),
                ('mistake', 'Типичная ошибка', '#F44336', 'fas fa-times-circle'),
                ('suggestion', 'Рекомендация', '#9C27B0', 'fas fa-lightbulb'),
            ]
            
            for i, (code, name, color, icon) in enumerate(comment_categories_data, 1):
                ReferenceItem.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        'name': name,
                        'order': i * 10,
                        'color': color,
                        'icon': icon,
                        'is_active': True
                    }
                )
