import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

# Импорты моделей
from curriculum.models import Topic, SubTopic, Course, CourseAssignment
from tasks.models import Task, TaskImage
from task_groups.models import AnalogGroup, TaskGroup
from works.models import Work, WorkAnalogGroup, Variant
from students.models import Student, StudentGroup
from events.models import Event, Mark

fake = Faker('ru_RU')

class Command(BaseCommand):
    help = 'Генерирует тестовые данные с упрощенной структурой Topic/SubTopic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tasks',
            type=int,
            default=80,
            help='Количество заданий для создания'
        )
        parser.add_argument(
            '--students',
            type=int,
            default=40,
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
            self.stdout.write('Создание тестовых данных с новой структурой Topic/SubTopic...')
            
            # Создаем данные в правильном порядке
            topics = self.create_topics()
            subtopics = self.create_subtopics(topics)
            tasks = self.create_tasks(options['tasks'], topics, subtopics)
            groups = self.create_analog_groups()
            self.link_tasks_to_groups(tasks, groups)
            
            works = self.create_works(groups)
            courses = self.create_courses()
            self.assign_works_to_courses(courses, works)
            variants = self.create_variants(works)
            
            students = self.create_students(options['students'])
            student_groups = self.create_student_groups(students)
            
            events = self.create_events(works, student_groups, courses)
            self.create_marks(events, variants, students)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано:\n'
                f'  - Тем: {len(topics)}\n'
                f'  - Подтем: {len(subtopics)}\n'
                f'  - Заданий: {len(tasks)}\n'
                f'  - Групп аналогов: {len(groups)}\n'
                f'  - Работ: {len(works)}\n'
                f'  - Курсов: {len(courses)}\n'
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
        CourseAssignment.objects.all().delete()
        Course.objects.all().delete()
        WorkAnalogGroup.objects.all().delete()
        Work.objects.all().delete()
        TaskGroup.objects.all().delete()
        AnalogGroup.objects.all().delete()
        Task.objects.all().delete()
        SubTopic.objects.all().delete()  # Сначала подтемы
        Topic.objects.all().delete()     # Потом темы
        StudentGroup.objects.all().delete()
        Student.objects.all().delete()
        self.stdout.write('Данные очищены.')

    def create_topics(self):
        """Создание основных тем (без иерархии)"""
        topics_data = [
            # Алгебра 8 класс
            ('algebra', 8, 'Алгебраические выражения', 'Многочлены и операции с ними', 1),
            ('algebra', 8, 'Алгебраические выражения', 'Формулы сокращенного умножения', 2),
            ('algebra', 8, 'Алгебраические выражения', 'Разложение на множители', 3),
            ('algebra', 8, 'Уравнения и неравенства', 'Линейные уравнения', 1),
            ('algebra', 8, 'Уравнения и неравенства', 'Квадратные уравнения', 2),
            ('algebra', 8, 'Уравнения и неравенства', 'Системы уравнений', 3),
            ('algebra', 8, 'Функции', 'Функция и её график', 1),
            
            # Алгебра 9 класс
            ('algebra', 9, 'Функции', 'Квадратичная функция', 1),
            ('algebra', 9, 'Функции', 'Степенная функция', 2),
            ('algebra', 9, 'Уравнения и неравенства', 'Неравенства второй степени', 1),
            ('algebra', 9, 'Последовательности', 'Арифметическая прогрессия', 1),
            ('algebra', 9, 'Последовательности', 'Геометрическая прогрессия', 2),
            
            # Геометрия 8 класс
            ('geometry', 8, 'Четырехугольники', 'Параллелограмм и его свойства', 1),
            ('geometry', 8, 'Четырехугольники', 'Прямоугольник и квадрат', 2),
            ('geometry', 8, 'Четырехугольники', 'Ромб и его свойства', 3),
            ('geometry', 8, 'Площади фигур', 'Площадь треугольника', 1),
            ('geometry', 8, 'Площади фигур', 'Площадь четырехугольника', 2),
            ('geometry', 8, 'Подобные треугольники', 'Признаки подобия', 1),
            
            # Геометрия 9 класс
            ('geometry', 9, 'Окружность', 'Вписанная окружность', 1),
            ('geometry', 9, 'Окружность', 'Описанная окружность', 2),
            ('geometry', 9, 'Векторы', 'Координаты вектора', 1),
            ('geometry', 9, 'Векторы', 'Скалярное произведение векторов', 2),
            ('geometry', 9, 'Движения', 'Центральная симметрия', 1),
        ]

        topics = []
        for subject, grade, section, name, order in topics_data:
            topic = Topic.objects.create(
                subject=subject,
                grade_level=grade,
                section=section,
                name=name,
                order=order,
                difficulty_level=random.randint(1, 3),
                description=f"Изучение темы '{name}' в рамках раздела '{section}' для {grade} класса"
            )
            topics.append(topic)
            self.stdout.write(f'  Создана тема: {topic}')

        return topics

    def create_subtopics(self, topics):
        """Создание подтем для основных тем"""
        subtopics_templates = {
            'Многочлены и операции с ними': [
                'Сложение и вычитание многочленов',
                'Умножение многочленов',
                'Деление многочленов'
            ],
            'Формулы сокращенного умножения': [
                'Квадрат суммы и разности',
                'Разность квадратов',
                'Куб суммы и разности'
            ],
            'Квадратные уравнения': [
                'Неполные квадратные уравнения',
                'Формула корней квадратного уравнения',
                'Теорема Виета',
                'Разложение квадратного трехчлена'
            ],
            'Параллелограмм и его свойства': [
                'Признаки параллелограмма',
                'Диагонали параллелограмма',
                'Площадь параллелограмма'
            ],
            'Квадратичная функция': [
                'График квадратичной функции',
                'Преобразования графика параболы',
                'Нули функции и промежутки знакопостоянства'
            ],
            'Арифметическая прогрессия': [
                'Формула n-го члена',
                'Сумма первых n членов',
                'Свойства арифметической прогрессии'
            ]
        }

        subtopics = []
        for topic in topics:
            if topic.name in subtopics_templates:
                # Создаем подтемы из шаблона
                subtopic_names = subtopics_templates[topic.name]
                for i, subtopic_name in enumerate(subtopic_names, 1):
                    subtopic = SubTopic.objects.create(
                        topic=topic,
                        name=subtopic_name,
                        order=i,
                        description=f"Подтема '{subtopic_name}' темы '{topic.name}'"
                    )
                    subtopics.append(subtopic)
                    self.stdout.write(f'    Создана подтема: {subtopic}')
            elif random.random() > 0.4:  # 60% вероятность создания подтем
                # Создаем 1-3 случайные подтемы
                num_subtopics = random.randint(1, 3)
                for i in range(num_subtopics):
                    subtopic = SubTopic.objects.create(
                        topic=topic,
                        name=f"{topic.name} - часть {i+1}",
                        order=i+1,
                        description=f"Дополнительные вопросы по теме '{topic.name}'"
                    )
                    subtopics.append(subtopic)
                    self.stdout.write(f'    Создана подтема: {subtopic}')

        return subtopics

    def create_tasks(self, count, topics, subtopics):
        """Создание заданий с привязкой к темам и подтемам"""
        task_types = ['computational', 'qualitative', 'theoretical', 'practical', 'test']
        cognitive_levels = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
        
        # Улучшенные шаблоны заданий
        algebra_templates = {
            'Квадратные уравнения': [
                'Решите уравнение: {a}x² + {b}x + {c} = 0',
                'Найдите дискриминант уравнения {a}x² + {b}x + {c} = 0',
                'При каких значениях параметра p уравнение x² + px + {a} = 0 имеет два корня?'
            ],
            'Формулы сокращенного умножения': [
                'Упростите выражение: ({a}x + {b})² - ({c}x - {d})²',
                'Разложите на множители: {a}x² - {b}',
                'Вычислите, используя формулы сокращенного умножения: {a}² - {b}²'
            ],
            'Арифметическая прогрессия': [
                'Найдите {n}-й член арифметической прогрессии, если a₁ = {a}, d = {b}',
                'Найдите сумму первых {n} членов арифметической прогрессии: {a}, {b}, {c}, ...',
                'Между числами {a} и {b} вставьте {n} чисел так, чтобы получилась арифметическая прогрессия'
            ]
        }
        
        geometry_templates = {
            'Параллелограмм и его свойства': [
                'В параллелограмме ABCD диагонали пересекаются в точке O. Найдите периметр треугольника AOB, если AB = {a} см, BC = {b} см, AC = {c} см',
                'Стороны параллелограмма равны {a} см и {b} см, угол между ними {c}°. Найдите площадь',
                'Диагонали параллелограмма равны {a} см и {b} см, угол между ними {c}°. Найдите площадь'
            ],
            'Площадь треугольника': [
                'Найдите площадь треугольника со сторонами {a} см, {b} см и {c} см',
                'В треугольнике ABC высота, проведенная к стороне BC, равна {a} см. Найдите площадь, если BC = {b} см',
                'Найдите площадь прямоугольного треугольника с катетами {a} см и {b} см'
            ]
        }

        tasks = []
        for i in range(count):
            # Выбираем случайную тему
            topic = random.choice(topics)
            subtopic = None
            
            # 40% вероятность выбрать подтему, если она есть
            if topic.subtopics.exists() and random.random() > 0.6:
                subtopic = random.choice(list(topic.subtopics.all()))

            # Генерируем текст задания
            text = self.generate_task_text(topic, algebra_templates, geometry_templates)
            
            # Генерируем ответ
            answer = self.generate_answer(text)

            task = Task.objects.create(
                text=text,
                answer=answer,
                short_solution=fake.text(max_nb_chars=150) if random.random() > 0.4 else '',
                full_solution=fake.text(max_nb_chars=400) if random.random() > 0.6 else '',
                hint=fake.sentence() if random.random() > 0.7 else '',
                topic=topic,
                subtopic=subtopic,
                task_type=random.choice(task_types),
                difficulty=random.randint(1, 5),
                cognitive_level=random.choice(cognitive_levels),
                estimated_time=random.randint(5, 30),
                content_element=f"{random.randint(1,9)}.{random.randint(1,9)}",
                requirement_element=f"{random.randint(1,5)}.{random.randint(1,9)}"
            )
            tasks.append(task)

        self.stdout.write(f'  Создано заданий: {len(tasks)}')
        return tasks

    def generate_task_text(self, topic, algebra_templates, geometry_templates):
        """Генерация текста задания в зависимости от темы"""
        # Ищем подходящие шаблоны
        template = None
        
        if topic.subject in ['algebra', 'mathematics']:
            for key in algebra_templates:
                if key.lower() in topic.name.lower():
                    template = random.choice(algebra_templates[key])
                    break
        elif topic.subject == 'geometry':
            for key in geometry_templates:
                if key.lower() in topic.name.lower():
                    template = random.choice(geometry_templates[key])
                    break
        
        if not template:
            # Общий шаблон
            template = f"Задание по теме '{topic.name}': {{text}}"

        # Подставляем случайные числа
        numbers = {
            'a': random.randint(1, 20),
            'b': random.randint(1, 20),
            'c': random.randint(1, 20),
            'd': random.randint(1, 20),
            'n': random.randint(5, 15),
            'text': fake.text(max_nb_chars=150)
        }
        
        try:
            return template.format(**numbers)
        except:
            return f"Задание по теме '{topic.name}': {fake.text(max_nb_chars=200)}"

    def generate_answer(self, text):
        """Генерация ответа в зависимости от типа задания"""
        text_lower = text.lower()
        
        if 'уравнение' in text_lower:
            return f"x = {random.randint(-10, 10)}"
        elif 'площадь' in text_lower:
            return f"{random.randint(10, 200)} см²"
        elif 'периметр' in text_lower:
            return f"{random.randint(20, 100)} см"
        elif 'найдите' in text_lower and 'член' in text_lower:
            return f"a_{random.randint(5, 20)} = {random.randint(10, 100)}"
        elif 'дискриминант' in text_lower:
            return f"D = {random.randint(1, 100)}"
        else:
            return fake.sentence(nb_words=random.randint(2, 8))

    def create_analog_groups(self):
        """Создание групп аналогичных заданий"""
        groups_data = [
            ('Линейные уравнения', 'Решение линейных уравнений с одной переменной'),
            ('Квадратные уравнения', 'Решение квадратных уравнений различными методами'),
            ('Системы уравнений', 'Решение систем линейных уравнений'),
            ('Неравенства', 'Решение линейных и квадратных неравенств'),
            ('Функции и графики', 'Построение и анализ графиков функций'),
            ('Многочлены', 'Операции с многочленами и их преобразования'),
            ('Геометрия - треугольники', 'Задачи на свойства треугольников'),
            ('Геометрия - четырехугольники', 'Задачи на параллелограммы и их виды'),
            ('Геометрия - окружности', 'Задачи на окружности и касательные'),
            ('Площади фигур', 'Вычисление площадей различных фигур'),
            ('Прогрессии', 'Арифметическая и геометрическая прогрессии'),
            ('Векторы', 'Операции с векторами и их применение'),
        ]

        groups = []
        for name, description in groups_data:
            group = AnalogGroup.objects.create(
                name=name,
                description=description
            )
            groups.append(group)

        self.stdout.write(f'  Создано групп аналогов: {len(groups)}')
        return groups

    def link_tasks_to_groups(self, tasks, groups):
        """Связывание заданий с группами аналогов"""
        for task in tasks:
            # Каждое задание добавляем в 1-2 группы на основе темы
            suitable_groups = []
            
            # Ищем подходящие группы по ключевым словам
            task_keywords = task.topic.name.lower()
            for group in groups:
                group_keywords = group.name.lower()
                if any(keyword in group_keywords for keyword in task_keywords.split()):
                    suitable_groups.append(group)
            
            # Если не нашли подходящие, берем случайные
            if not suitable_groups:
                suitable_groups = random.sample(groups, min(2, len(groups)))
            
            # Добавляем в 1-2 группы
            selected_groups = random.sample(suitable_groups, min(random.randint(1, 2), len(suitable_groups)))
            
            for group in selected_groups:
                TaskGroup.objects.get_or_create(task=task, group=group)

    # Остальные методы остаются такими же как в предыдущей версии
    def create_works(self, groups):
        """Создание работ"""
        works_data = [
            ('Контрольная работа №1 "Квадратные уравнения"', 45, 'test'),
            ('Самостоятельная работа "Системы уравнений"', 30, 'quiz'),
            ('Зачет по геометрии "Четырехугольники"', 60, 'test'),
            ('Итоговая контрольная работа за четверть', 90, 'exam'),
            ('Диагностическая работа "Функции"', 40, 'diagnostic'),
            ('Домашняя работа "Прогрессии"', 60, 'homework'),
            ('Практическая работа "Площади фигур"', 45, 'practice'),
        ]

        works = []
        for name, duration, work_type in works_data:
            work = Work.objects.create(
                name=name, 
                duration=duration,
                work_type=work_type
            )
            
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

    def create_courses(self):
        """Создание курсов"""
        courses_data = [
            ('Алгебра 8 класс', 'algebra', 8, '2024-2025', 'Базовый курс алгебры для 8 класса'),
            ('Геометрия 8 класс', 'geometry', 8, '2024-2025', 'Базовый курс геометрии для 8 класса'),
            ('Алгебра 9 класс', 'algebra', 9, '2024-2025', 'Курс алгебры для 9 класса с подготовкой к ОГЭ'),
            ('Геометрия 9 класс', 'geometry', 9, '2024-2025', 'Курс геометрии для 9 класса с подготовкой к ОГЭ'),
            ('Математика 8 класс (углубленный)', 'mathematics', 8, '2024-2025', 'Углубленный курс математики'),
        ]

        courses = []
        for name, subject, grade, year, description in courses_data:
            course = Course.objects.create(
                name=name,
                subject=subject,
                grade_level=grade,
                academic_year=year,
                description=description,
                start_date=date(2024, 9, 1),
                end_date=date(2025, 5, 31),
                total_hours=random.randint(100, 200),
                hours_per_week=random.randint(2, 5),
                is_active=True
            )
            courses.append(course)

        self.stdout.write(f'  Создано курсов: {len(courses)}')
        return courses

    def assign_works_to_courses(self, courses, works):
        """Назначение работ в курсы"""
        for course in courses:
            # Каждому курсу назначаем 3-5 работ
            course_works = random.sample(works, random.randint(3, min(5, len(works))))
            
            for i, work in enumerate(course_works, 1):
                CourseAssignment.objects.create(
                    course=course,
                    work=work,
                    order=i,
                    planned_date=course.start_date + timedelta(days=random.randint(1, 200)),
                    weight=round(random.uniform(0.5, 2.0), 1)
                )

    def create_variants(self, works):
        """Создание вариантов для работ"""
        variants = []
        for work in works:
            num_variants = random.randint(4, 6)
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
        
        students_per_class = len(students) // len(class_names)
        
        for i, class_name in enumerate(class_names):
            start_idx = i * students_per_class
            end_idx = start_idx + students_per_class if i < len(class_names) - 1 else len(students)
            
            student_group = StudentGroup.objects.create(name=class_name)
            student_group.students.set(students[start_idx:end_idx])
            student_groups.append(student_group)

        self.stdout.write(f'  Создано классов: {len(student_groups)}')
        return student_groups

    def create_events(self, works, student_groups, courses):
        """Создание событий"""
        statuses = ['planned', 'conducted', 'checked', 'graded', 'closed']
        events = []
        
        for work in works:
            for student_group in random.sample(student_groups, random.randint(1, 2)):
                course = None
                matching_courses = [c for c in courses 
                                  if str(student_group.name[0]) == str(c.grade_level)]
                if matching_courses:
                    course = random.choice(matching_courses)
                
                event = Event.objects.create(
                    name=f"{work.name} - {student_group.name}",
                    date=fake.date_time_between(start_date='-30d', end_date='+30d'),
                    work=work,
                    student_group=student_group,
                    status=random.choice(statuses),
                    course=course,
                    planned_date=fake.date_time_between(start_date='-30d', end_date='+30d'),
                    actual_date=fake.date_time_between(start_date='-30d', end_date='+30d') if random.random() > 0.3 else None
                )
                events.append(event)

        self.stdout.write(f'  Создано событий: {len(events)}')
        return events

    def create_marks(self, events, variants, students):
        """Создание отметок"""
        marks_count = 0
        
        for event in events:
            if event.status in ['conducted', 'checked', 'graded', 'closed']:
                class_students = list(event.student_group.students.all())
                available_variants = [v for v in variants if v.work == event.work]
                
                if available_variants and class_students:
                    for student in class_students:
                        if random.random() > 0.1:  # 90% учеников выполняют работу
                            variant = random.choice(available_variants)
                            score = None
                            
                            if event.status in ['graded', 'closed']:
                                score = random.randint(2, 5)
                            
                            Mark.objects.create(
                                student=student,
                                variant=variant,
                                event=event,
                                score=score
                            )
                            marks_count += 1

        self.stdout.write(f'  Создано отметок: {marks_count}')
