import random
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

# Импорты моделей
from tasks.models import Task, TaskImage
from task_groups.models import AnalogGroup, TaskGroup
from works.models import Work, WorkAnalogGroup, Variant
from students.models import Student, StudentGroup
from events.models import Event, Mark

fake = Faker('ru_RU')  # Русская локализация

class Command(BaseCommand):
    help = 'Генерирует тестовые данные для приложения'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tasks',
            type=int,
            default=50,
            help='Количество заданий для создания'
        )
        parser.add_argument(
            '--students',
            type=int,
            default=30,
            help='Количество учеников для создания'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить все данные перед генерацией'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очистка существующих данных...')
            self.clear_data()

        with transaction.atomic():
            self.stdout.write('Создание тестовых данных...')
            
            # Создаем данные в правильном порядке
            groups = self.create_analog_groups()
            tasks = self.create_tasks(options['tasks'])
            self.link_tasks_to_groups(tasks, groups)
            
            works = self.create_works(groups)
            variants = self.create_variants(works)
            
            students = self.create_students(options['students'])
            student_groups = self.create_student_groups(students)
            
            events = self.create_events(works, student_groups)
            self.create_marks(events, variants, students)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано:\n'
                f'  - Заданий: {len(tasks)}\n'
                f'  - Групп аналогов: {len(groups)}\n'
                f'  - Работ: {len(works)}\n'
                f'  - Вариантов: {sum(len(work.variant_set.all()) for work in works)}\n'
                f'  - Учеников: {len(students)}\n'
                f'  - Классов: {len(student_groups)}\n'
                f'  - Событий: {len(events)}'
            )
        )

    def clear_data(self):
        """Очистка всех тестовых данных"""
        Mark.objects.all().delete()
        Event.objects.all().delete()
        Variant.objects.all().delete()
        WorkAnalogGroup.objects.all().delete()
        Work.objects.all().delete()
        TaskGroup.objects.all().delete()
        AnalogGroup.objects.all().delete()
        Task.objects.all().delete()
        StudentGroup.objects.all().delete()
        Student.objects.all().delete()
        self.stdout.write('Данные очищены.')

    def create_analog_groups(self):
        """Создание групп аналогичных заданий"""
        groups_data = [
            ('Линейные уравнения', 'Решение линейных уравнений с одной переменной'),
            ('Квадратные уравнения', 'Решение квадратных уравнений различными методами'),
            ('Системы уравнений', 'Решение систем линейных уравнений'),
            ('Неравенства', 'Решение линейных и квадратных неравенств'),
            ('Функции и графики', 'Построение и анализ графиков функций'),
            ('Геометрия - треугольники', 'Задачи на свойства треугольников'),
            ('Геометрия - окружности', 'Задачи на окружности и касательные'),
            ('Проценты', 'Задачи на проценты и пропорции'),
            ('Текстовые задачи', 'Задачи на движение, работу, смеси'),
            ('Степени и корни', 'Преобразование выражений со степенями'),
        ]

        groups = []
        for name, description in groups_data:
            group = AnalogGroup.objects.create(
                name=name,
                description=description
            )
            groups.append(group)
            self.stdout.write(f'  Создана группа: {name}')

        return groups

    def create_tasks(self, count):
        """Создание заданий"""
        sections = ['Алгебра', 'Геометрия', 'Математический анализ']
        task_types = ['computational', 'qualitative', 'theoretical', 'practical']
        difficulties = [1, 2, 3, 4, 5]

        # Примеры заданий для разных типов
        task_templates = {
            'Линейные уравнения': [
                'Решите уравнение: {a}x + {b} = {c}',
                'Найдите корень уравнения: {a}x - {b} = {c}x + {d}',
                'При каком значении x выражение {a}x + {b} равно {c}?'
            ],
            'Квадратные уравнения': [
                'Решите уравнение: {a}x² + {b}x + {c} = 0',
                'Найдите дискриминант уравнения {a}x² + {b}x + {c} = 0',
                'Разложите на множители: {a}x² + {b}x + {c}'
            ],
            'Геометрия - треугольники': [
                'В треугольнике ABC угол A = {a}°, угол B = {b}°. Найдите угол C.',
                'Стороны треугольника равны {a} см, {b} см и {c} см. Найдите периметр.',
                'В прямоугольном треугольнике катеты равны {a} и {b}. Найдите гипотенузу.'
            ],
            'Проценты': [
                'Найдите {a}% от числа {b}',
                'Число увеличили на {a}%. Получили {b}. Найдите первоначальное число.',
                'Цена товара была {a} рублей. После скидки {b}% она стала равна...'
            ]
        }

        tasks = []
        for i in range(count):
            # Случайные параметры
            section = random.choice(sections)
            topic = fake.sentence(nb_words=3).replace('.', '')
            task_type = random.choice(task_types)
            difficulty = random.choice(difficulties)

            # Генерируем текст задания
            if i < 30:  # Первые 30 заданий делаем более реалистичными
                group_names = list(task_templates.keys())
                chosen_group = random.choice(group_names)
                template = random.choice(task_templates[chosen_group])
                
                # Подставляем случайные числа
                numbers = {
                    'a': random.randint(1, 20),
                    'b': random.randint(1, 20), 
                    'c': random.randint(1, 20),
                    'd': random.randint(1, 20)
                }
                text = template.format(**numbers)
                topic = chosen_group
            else:
                # Остальные задания генерируем случайно
                text = f"Задание {i+1}: {fake.text(max_nb_chars=200)}"

            # Генерируем ответ
            if 'уравнение' in text.lower():
                answer = f"x = {random.randint(-10, 10)}"
            elif 'найдите' in text.lower():
                answer = f"{random.randint(1, 100)}"
            else:
                answer = fake.sentence(nb_words=random.randint(2, 8))

            task = Task.objects.create(
                text=text,
                answer=answer,
                short_solution=fake.text(max_nb_chars=100) if random.random() > 0.3 else '',
                full_solution=fake.text(max_nb_chars=300) if random.random() > 0.5 else '',
                hint=fake.sentence() if random.random() > 0.6 else '',
                section=section,
                topic=topic,
                subtopic=fake.word() if random.random() > 0.5 else '',
                task_type=task_type,
                difficulty=difficulty,
                content_element=f"{random.randint(1,9)}.{random.randint(1,9)}",
                requirement_element=f"{random.randint(1,5)}.{random.randint(1,9)}"
            )
            tasks.append(task)

        self.stdout.write(f'  Создано заданий: {len(tasks)}')
        return tasks

    def link_tasks_to_groups(self, tasks, groups):
        """Связывание заданий с группами аналогов"""
        for task in tasks:
            # Каждое задание добавляем в 1-3 группы
            num_groups = random.randint(1, 3)
            selected_groups = random.sample(groups, min(num_groups, len(groups)))
            
            for group in selected_groups:
                TaskGroup.objects.get_or_create(task=task, group=group)

    def create_works(self, groups):
        """Создание работ"""
        works_data = [
            ('Контрольная работа №1 "Линейные уравнения"', 45),
            ('Самостоятельная работа "Квадратные уравнения"', 30),
            ('Зачет по геометрии', 60),
            ('Итоговая контрольная работа', 90),
            ('Диагностическая работа', 40),
        ]

        works = []
        for name, duration in works_data:
            work = Work.objects.create(name=name, duration=duration)
            
            # Добавляем 2-4 группы заданий в каждую работу
            selected_groups = random.sample(groups, random.randint(2, 4))
            for group in selected_groups:
                WorkAnalogGroup.objects.create(
                    work=work,
                    analog_group=group,
                    count=random.randint(1, 3)
                )
            
            works.append(work)

        self.stdout.write(f'  Создано работ: {len(works)}')
        return works

    def create_variants(self, works):
        """Создание вариантов для работ"""
        variants = []
        for work in works:
            # Создаем 4-8 вариантов для каждой работы
            num_variants = random.randint(4, 8)
            new_variants = work.generate_variants(num_variants)
            variants.extend(new_variants)

        self.stdout.write(f'  Создано вариантов: {len(variants)}')
        return variants

    def create_students(self, count):
        """Создание учеников"""
        students = []
        for _ in range(count):
            student = Student.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                middle_name=fake.middle_name() if random.random() > 0.3 else '',
                email=fake.email() if random.random() > 0.5 else ''
            )
            students.append(student)

        self.stdout.write(f'  Создано учеников: {len(students)}')
        return students

    def create_student_groups(self, students):
        """Создание классов"""
        class_names = ['8А', '8Б', '9А', '9Б', '10А']
        student_groups = []
        
        # Разделяем учеников по классам
        students_per_class = len(students) // len(class_names)
        
        for i, class_name in enumerate(class_names):
            start_idx = i * students_per_class
            end_idx = start_idx + students_per_class if i < len(class_names) - 1 else len(students)
            
            student_group = StudentGroup.objects.create(name=class_name)
            student_group.students.set(students[start_idx:end_idx])
            student_groups.append(student_group)

        self.stdout.write(f'  Создано классов: {len(student_groups)}')
        return student_groups

    def create_events(self, works, student_groups):
        """Создание событий"""
        statuses = ['planned', 'conducted', 'checked', 'graded', 'closed']
        events = []
        
        for work in works:
            # Создаем событие для каждого класса
            for student_group in random.sample(student_groups, random.randint(1, 3)):
                event = Event.objects.create(
                    name=f"{work.name} - {student_group.name}",
                    date=fake.date_time_between(start_date='-30d', end_date='+30d'),
                    work=work,
                    student_group=student_group,
                    status=random.choice(statuses)
                )
                events.append(event)

        self.stdout.write(f'  Создано событий: {len(events)}')
        return events

    def create_marks(self, events, variants, students):
        """Создание отметок"""
        marks_count = 0
        
        for event in events:
            if event.status in ['conducted', 'checked', 'graded', 'closed']:
                # Создаем отметки для учеников класса
                class_students = list(event.student_group.students.all())
                available_variants = [v for v in variants if v.work == event.work]
                
                if available_variants and class_students:
                    for student in class_students:
                        if random.random() > 0.1:  # 90% учеников выполняют работу
                            variant = random.choice(available_variants)
                            score = None
                            
                            if event.status in ['graded', 'closed']:
                                score = random.randint(2, 5)  # Оценки от 2 до 5
                            
                            Mark.objects.create(
                                student=student,
                                variant=variant,
                                event=event,
                                score=score
                            )
                            marks_count += 1

        self.stdout.write(f'  Создано отметок: {marks_count}')
