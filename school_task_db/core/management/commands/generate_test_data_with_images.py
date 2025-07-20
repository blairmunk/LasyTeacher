import os
import random
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

class Command(BaseCommand):
    help = 'Генерация тестовых данных с изображениями для проверки LaTeX minipage'

    def add_arguments(self, parser):
        parser.add_argument('--tasks', type=int, default=12, help='Количество заданий с изображениями')
        parser.add_argument('--clear', action='store_true', help='Очистить старые данные')
        parser.add_argument('--no-images', action='store_true', help='Не генерировать изображения (только данные)')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🧹 Очистка старых данных...')
            self.clear_old_data()

        self.stdout.write('🎨 Генерация тестовых данных с изображениями...')
        
        # Создаем папки для изображений
        self.setup_media_dirs()
        
        with transaction.atomic():
            # Создаем базовые данные
            topics = self.create_test_topics()
            
            # Генерируем изображения (если нужно)
            if not options['no_images']:
                self.check_imagemagick()
                images_created = self.generate_test_images()
                self.stdout.write(f'🖼️ Сгенерировано изображений: {images_created}')
            
            # Создаем задания с изображениями
            tasks = self.create_tasks_with_images(options['tasks'], topics)
            
            # Создаем работу и варианты для тестирования
            work = self.create_test_work(tasks)
            
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Готово!\n'
                f'  • Создано заданий с изображениями: {len(tasks)}\n'
                f'  • Создана тестовая работа: {work.name}\n'
                f'  • ID работы для тестирования: {work.id}\n\n'
                f'🚀 Для тестирования запустите:\n'
                f'   python manage.py generate_latex work {work.id} --format pdf'
            )
        )

    def clear_old_data(self):
        """Очистка старых тестовых данных с проверкой существования таблиц"""
        # Импорты только при использовании
        try:
            from tasks.models import Task, TaskImage
            from curriculum.models import Topic, SubTopic
            from students.models import Student, StudentGroup
            from task_groups.models import AnalogGroup, TaskGroup
            from works.models import Work, WorkAnalogGroup, Variant
            from events.models import Event, EventParticipation, Mark
            
            # Проверяем что таблицы существуют
            from django.db import connection
            existing_tables = connection.introspection.table_names()
            
            # Очищаем только если таблицы существуют
            if 'tasks_taskimage' in existing_tables:
                TaskImage.objects.filter(task__text__contains='ТЕСТ').delete()
            
            if 'tasks_task' in existing_tables:
                Task.objects.filter(text__contains='ТЕСТ').delete()
            
            if 'curriculum_topic' in existing_tables:
                Topic.objects.filter(name__contains='ТЕСТ').delete()
            
            if 'works_work' in existing_tables:
                Work.objects.filter(name__contains='ТЕСТ').delete()
            
            self.stdout.write('✅ Очистка данных завершена')
            
        except Exception as e:
            self.stdout.write(f'⚠️ Ошибка при очистке: {e}')
            self.stdout.write('Продолжаем без очистки...')


    def setup_media_dirs(self):
        """Создание папок для медиа файлов"""
        media_dir = Path(settings.MEDIA_ROOT) / 'task_images'
        media_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir = media_dir

    def check_imagemagick(self):
        """Проверка наличия ImageMagick"""
        try:
            result = subprocess.run(['convert', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write('✅ ImageMagick найден')
                return True
        except FileNotFoundError:
            pass
        
        self.stdout.write(
            self.style.WARNING(
                '⚠️ ImageMagick не найден. Установите:\n'
                '   Ubuntu/Debian: sudo apt-get install imagemagick\n'
                '   CentOS/RHEL: sudo yum install ImageMagick\n'
                '   macOS: brew install imagemagick'
            )
        )
        return False

    def generate_test_images(self):
        """Генерация тестовых изображений с помощью ImageMagick"""
        
        # Математические формулы и выражения для изображений
        math_formulas = [
            'x² + 2x + 1 = 0',
            '∫ x² dx = x³/3 + C',
            'sin²α + cos²α = 1',
            'lim(x→0) sin(x)/x = 1',
            'a² + b² = c²',
            'f(x) = ax² + bx + c',
            'log₂(8) = 3',
            '√(x² + y²)',
            'Σ(i=1 to n) i = n(n+1)/2',
            'e^(iπ) + 1 = 0',
            'dy/dx = 2x + 3',
            '|x - 2| < 5'
        ]
        
        # Геометрические фигуры (описания для создания)
        geometry_figures = [
            'Треугольник ABC',
            'Окружность с центром O',
            'Параллелограмм ABCD',
            'Координатная плоскость',
            'График функции y=x²',
            'Прямоугольник 4×3'
        ]
        
        # Физические схемы
        physics_diagrams = [
            'Схема электрической цепи',
            'Рычаг с грузами',
            'Траектория движения',
            'Колебания маятника'
        ]
        
        all_content = math_formulas + geometry_figures + physics_diagrams
        
        created_count = 0
        
        for i, content in enumerate(all_content, 1):
            filename = f'test_image_{i:02d}.png'
            filepath = self.media_dir / filename
            
            # Создаем изображение с текстом
            success = self.create_image_with_text(
                text=content,
                output_path=str(filepath),
                width=400,
                height=300,
                font_size=20
            )
            
            if success:
                created_count += 1
                if i <= 3:  # Показываем прогресс для первых 3
                    self.stdout.write(f'  📸 Создано: {filename} ({content[:30]}...)')
        
        return created_count

    def create_image_with_text(self, text, output_path, width=400, height=300, font_size=20):
        """Создание изображения с текстом используя ImageMagick"""
        try:
            # Команда ImageMagick для создания изображения с текстом
            cmd = [
                'convert',
                '-size', f'{width}x{height}',
                'xc:white',  # Белый фон
                '-fill', 'black',
                '-font', 'DejaVu-Sans',  # Шрифт поддерживающий математические символы
                '-pointsize', str(font_size),
                '-gravity', 'center',
                '-annotate', '0', text,
                '-border', '10',
                '-bordercolor', 'lightgray',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                # Пробуем упрощенную версию если не получилось
                simple_cmd = [
                    'convert',
                    '-size', f'{width}x{height}',
                    'xc:white',
                    '-fill', 'black',
                    '-pointsize', str(font_size),
                    '-gravity', 'center',
                    '-annotate', '0', text,
                    output_path
                ]
                
                simple_result = subprocess.run(simple_cmd, capture_output=True, text=True)
                return simple_result.returncode == 0
                
        except Exception as e:
            self.stdout.write(f'❌ Ошибка создания изображения {output_path}: {e}')
            return False

    def create_test_topics(self):
        """Создание тестовых тем"""
        from curriculum.models import Topic, SubTopic
        
        topics_data = [
            ('mathematics', 8, 'Алгебра', 'ТЕСТ: Квадратные уравнения'),
            ('mathematics', 9, 'Алгебра', 'ТЕСТ: Функции и графики'),
            ('geometry', 8, 'Планиметрия', 'ТЕСТ: Четырехугольники'),
            ('physics', 9, 'Механика', 'ТЕСТ: Кинематика'),
        ]
        
        topics = []
        for subject, grade, section, name in topics_data:
            topic, created = Topic.objects.get_or_create(
                name=name,
                subject=subject,
                grade_level=grade,
                section=section,
                defaults={
                    'order': len(topics) + 1,
                    'difficulty_level': 2,
                    'description': f'Тестовая тема для проверки LaTeX генерации: {name}'
                }
            )
            topics.append(topic)
            
            if created:
                # Создаем 2 подтемы для каждой темы
                for j in range(2):
                    SubTopic.objects.get_or_create(
                        topic=topic,
                        name=f'Подтема {j+1}',
                        defaults={
                            'order': j+1,
                            'description': f'Тестовая подтема {j+1} для {topic.name}'
                        }
                    )
        
        return topics

    def create_tasks_with_images(self, count, topics):
        """Создание заданий с изображениями"""
        from tasks.models import Task, TaskImage
        
        # Позиции для изображений (все варианты minipage)
        positions = ['right_40', 'right_20', 'bottom_100', 'bottom_70']
        
        # Типы заданий с изображениями
        task_templates = [
            'ТЕСТ: Решите квадратное уравнение {}. Постройте график функции.',
            'ТЕСТ: На рисунке изображена схема {}. Найдите указанные элементы.',
            'ТЕСТ: Исследуйте функцию {} и постройте её график.',
            'ТЕСТ: По данной схеме {} определите физические величины.',
            'ТЕСТ: Докажите равенство {} используя свойства фигур.',
            'ТЕСТ: Вычислите значение выражения {} при заданных условиях.',
            'ТЕСТ: Проанализируйте график {} и найдите область определения.',
            'ТЕСТ: Используя формулу {}, решите практическую задачу.',
            'ТЕСТ: На диаграмме показана зависимость {}. Сделайте выводы.',
            'ТЕСТ: Постройте модель {} согласно условиям задачи.',
            'ТЕСТ: Определите параметры {} по приведенному чертежу.',
            'ТЕСТ: Исследуйте поведение {} в заданном интервале.'
        ]
        
        # Ответы соответствующие типам заданий
        answer_templates = [
            'x₁ = -1, x₂ = -1',
            'Элементы найдены верно',
            'Функция убывает на (-∞; 0], возрастает на [0; +∞)',
            'U = 12В, I = 2А, R = 6Ом',
            'Доказательство через равенство углов',
            '42',
            'D(f) = (-∞; +∞), E(f) = [0; +∞)',
            'Ответ: 15 метров',
            'График показывает линейную зависимость',
            'Модель построена согласно условиям',
            'a = 5, b = 3, c = 4',
            'Функция имеет максимум в точке x = 2'
        ]
        
        tasks = []
        available_images = list(self.media_dir.glob('test_image_*.png'))
        
        if not available_images:
            self.stdout.write(
                self.style.WARNING('⚠️ Изображения не найдены. Создание заданий без изображений.')
            )
        
        for i in range(count):
            # Выбираем случайную тему
            topic = random.choice(topics)
            subtopic = None
            if topic.subtopics.exists() and random.random() > 0.5:
                subtopic = random.choice(list(topic.subtopics.all()))
            
            # Создаем задание
            template_idx = i % len(task_templates)
            formula_placeholder = f"формулы_{i+1}"
            
            task = Task.objects.create(
                text=task_templates[template_idx].format(formula_placeholder),
                answer=answer_templates[template_idx],
                topic=topic,
                subtopic=subtopic,
                task_type='practical',
                difficulty=random.randint(2, 4),
                cognitive_level='apply',
                estimated_time=random.choice([10, 15, 20, 25]),
                short_solution=f'ТЕСТ: Краткое решение для задания {i+1}',
                full_solution=f'ТЕСТ: Подробное решение для задания {i+1} с пояснениями шагов.',
                hint=f'ТЕСТ: Подсказка {i+1} - обратите внимание на изображение',
            )
            
            # Добавляем изображение к заданию
            if available_images:
                image_file = available_images[i % len(available_images)]
                position = positions[i % len(positions)]
                
                # Создаем относительный путь для сохранения в базе
                relative_path = f'task_images/{image_file.name}'
                
                TaskImage.objects.create(
                    task=task,
                    image=relative_path,
                    position=position,
                    caption=f'ТЕСТ: Рисунок {i+1} - {position}',
                    order=1
                )
                
                self.stdout.write(f'  📝 Задание {i+1}: {position} - {task.text[:50]}...')
            
            tasks.append(task)
        
        return tasks

    def create_test_work(self, tasks):
        """Создание тестовой работы с вариантами"""
        from works.models import Work
        from task_groups.models import AnalogGroup, TaskGroup
        
        # Создаем группу аналогов
        group, created = AnalogGroup.objects.get_or_create(
            name='ТЕСТ: Группа заданий с изображениями',
            defaults={
                'description': 'Тестовая группа для проверки LaTeX генерации с minipage'
            }
        )
        
        # Добавляем все задания в группу
        for task in tasks:
            TaskGroup.objects.get_or_create(task=task, group=group)
        
        # Создаем работу
        work, created = Work.objects.get_or_create(
            name='ТЕСТ: Контрольная работа с изображениями',
            defaults={
                'duration': 45,
                'work_type': 'test'
            }
        )
        
        if created:
            # Добавляем группу в работу
            from works.models import WorkAnalogGroup
            WorkAnalogGroup.objects.get_or_create(
                work=work,
                analog_group=group,
                defaults={'count': 3}  # По 3 задания в каждом варианте
            )
        
        # Генерируем варианты
        if not work.variant_set.exists():
            work.generate_variants(4)
            self.stdout.write(f'  📋 Создано 4 варианта для работы {work.name}')
        
        return work
