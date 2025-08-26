"""
Команда для глубокого наполнения базы тестовыми данными
Использует все возможности моделей с реалистичными связями
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

# Импорты всех моделей
from references.models import SimpleReference, SubjectReference
from curriculum.models import Topic, SubTopic, Course, CourseAssignment
from tasks.models import Task, TaskImage
from task_groups.models import AnalogGroup, TaskGroup
from works.models import Work, WorkAnalogGroup, Variant
from students.models import Student, StudentGroup
from events.models import Event, EventParticipation, Mark
from review.models import ReviewSession, ReviewComment

class Command(BaseCommand):
    help = 'Создает полную базу тестовых данных для школьной системы'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Удалить все существующие данные')
        parser.add_argument('--size', choices=['small', 'medium', 'large'], default='medium', 
                          help='Размер тестовых данных')
        parser.add_argument('--export-json', type=str, help='Экспортировать созданные данные в JSON файл')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_database()
        
        # Определяем размеры данных
        sizes = {
            'small': {'students': 30, 'tasks': 100, 'works': 5},
            'medium': {'students': 150, 'tasks': 500, 'works': 20}, 
            'large': {'students': 500, 'tasks': 2000, 'works': 50}
        }
        
        self.size_config = sizes[options['size']]
        
        with transaction.atomic():
            self.stdout.write(f"🚀 Создание {options['size']} набора тестовых данных...")
            
            # Порядок создания учитывает зависимости
            self.create_references()
            self.create_curriculum()  
            self.create_tasks()
            self.create_task_groups()
            self.create_works()
            self.create_students()
            self.create_courses()
            self.create_events()
            self.create_reviews()
            
            self.stdout.write(self.style.SUCCESS("🎉 База данных успешно наполнена!"))
            
            if options['export_json']:
                self.export_to_json(options['export_json'])

    def clear_database(self):
        """Очистка всех данных"""
        self.stdout.write("🗑️ Очистка базы данных...")
        
        # Порядок удаления (обратный зависимостям)
        models_to_clear = [
            ReviewSession, ReviewComment, Mark, 
            EventParticipation, Event,
            CourseAssignment, Course,
            Variant, WorkAnalogGroup, Work,
            TaskGroup, AnalogGroup,
            TaskImage, Task,
            SubTopic, Topic,
            StudentGroup, Student,
            SubjectReference, SimpleReference
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(f"   Удалено {count} записей {model.__name__}")

    def create_references(self):
        """Создание справочников"""
        self.stdout.write("📚 Создание справочников...")
        
        # Простые справочники
        references = {
            'subjects': 'Математика\nФизика\nХимия\nИнформатика\nБиология',
            'task_types': 'Расчётная задача\nКачественная задача\nТеоретический вопрос\nПрактическое задание\nТестовое задание',
            'difficulty_levels': 'Подготовительный\nБазовый\nПовышенный\nВысокий\nЭкспертный',
            'cognitive_levels': 'Запоминание\nПонимание\nПрименение\nАнализ\nОценка\nСоздание',
            'work_types': 'Контрольная работа\nСамостоятельная работа\nДиагностическая работа\nЭкзамен\nДомашнее задание',
            'comment_categories': 'Отличная работа\nХорошая работа\nТребует улучшения\nТипичная ошибка\nРекомендация'
        }
        
        for category, items_text in references.items():
            SimpleReference.objects.get_or_create(
                category=category,
                defaults={'items_text': items_text}
            )
        
        # Кодификаторы по предметам
        math_content = """1.1|Натуральные числа
1.2|Обыкновенные дроби  
1.3|Десятичные дроби
2.1|Алгебраические выражения
2.2|Уравнения
2.3|Неравенства
3.1|Функции и их свойства
3.2|Графики функций
4.1|Геометрические фигуры
4.2|Площади и объемы"""

        physics_content = """1.1|Механическое движение
1.2|Силы в природе
1.3|Законы сохранения
2.1|Молекулярная физика
2.2|Термодинамика
3.1|Электрические явления
3.2|Магнитные явления"""

        SubjectReference.objects.get_or_create(
            subject='Математика',
            grade_level='7-11',
            category='content_elements',
            defaults={'items_text': math_content}
        )
        
        SubjectReference.objects.get_or_create(
            subject='Физика', 
            grade_level='7-11',
            category='content_elements',
            defaults={'items_text': physics_content}
        )

    def create_curriculum(self):
        """Создание учебной программы"""
        self.stdout.write("🎓 Создание учебной программы...")
        
        # Темы по математике
        math_topics_data = [
            (7, 'Алгебра', [
                ('Алгебраические выражения', ['Одночлены', 'Многочлены', 'Формулы сокращенного умножения']),
                ('Линейные уравнения', ['Решение уравнений', 'Текстовые задачи', 'Системы уравнений']),
                ('Функции', ['Линейная функция', 'График функции', 'Область определения'])
            ]),
            (8, 'Алгебра', [
                ('Квадратные корни', ['Арифметический корень', 'Свойства корней', 'Преобразования']),
                ('Квадратные уравнения', ['Формула корней', 'Теорема Виета', 'Задачи на движение']),
                ('Неравенства', ['Линейные неравенства', 'Квадратные неравенства', 'Системы неравенств'])
            ]),
            (9, 'Алгебра', [
                ('Функции и их свойства', ['Область определения', 'Монотонность', 'Экстремумы']),
                ('Прогрессии', ['Арифметическая прогрессия', 'Геометрическая прогрессия', 'Сумма прогрессии']),
                ('Тригонометрия', ['Синус и косинус', 'Основное тригонометрическое тождество', 'Формулы приведения'])
            ]),
            (7, 'Геометрия', [
                ('Треугольники', ['Признаки равенства', 'Равнобедренный треугольник', 'Прямоугольный треугольник']),
                ('Параллельные прямые', ['Признаки параллельности', 'Свойства параллельных прямых', 'Углы при параллельных'])
            ]),
            (8, 'Геометрия', [
                ('Четырехугольники', ['Параллелограмм', 'Ромб', 'Прямоугольник', 'Квадрат', 'Трапеция']),
                ('Площадь', ['Площадь треугольника', 'Площадь параллелограмма', 'Площадь трапеции'])
            ])
        ]
        
        # Физические темы  
        physics_topics_data = [
            (7, 'Механика', [
                ('Механическое движение', ['Равномерное движение', 'Скорость', 'Путь и перемещение']),
                ('Взаимодействие тел', ['Сила', 'Масса', 'Плотность', 'Сила тяжести'])
            ]),
            (8, 'Тепловые явления', [
                ('Внутренняя энергия', ['Способы изменения внутренней энергии', 'Теплопроводность', 'Конвекция']),
                ('Изменения агрегатных состояний', ['Плавление', 'Парообразование', 'Удельная теплота'])
            ])
        ]
        
        self.topics = {}
        
        for grade, section, topics_list in math_topics_data + physics_topics_data:
            subject = 'Математика' if section in ['Алгебра', 'Геометрия'] else 'Физика'
            
            for topic_name, subtopic_names in topics_list:
                topic = Topic.objects.create(
                    name=topic_name,
                    subject=subject,
                    section=section,
                    grade_level=grade,
                    order=len(self.topics) + 1,
                    description=f"Изучение {topic_name.lower()} в {grade} классе"
                )
                
                self.topics[f"{subject}_{grade}_{topic_name}"] = topic
                
                # Создаем подтемы
                for i, subtopic_name in enumerate(subtopic_names, 1):
                    SubTopic.objects.create(
                        topic=topic,
                        name=subtopic_name,
                        order=i,
                        description=f"Подтема: {subtopic_name}"
                    )

    def create_tasks(self):
        """Создание заданий"""
        self.stdout.write("📝 Создание заданий...")
        
        # ДОБАВЛЕНО: Проверяем что темы созданы
        topics_count = len(self.topics)
        if topics_count == 0:
            self.stdout.write("   ❌ Темы не созданы - создание заданий невозможно")
            self.tasks = []
            return
        
        self.stdout.write(f"   Доступно тем: {topics_count}")
        
        # ДОБАВЛЕНО: Шаблоны заданий (было пропущено)
        task_templates = [
            # Математические задания
            {
                'templates': [
                    "Решите уравнение: ${}x + {} = {}$",
                    "Найдите значение выражения: $({})^2 - {} \\cdot {} + {}$",
                    "Упростите выражение: $\\frac{{{}x + {}}}{{{}x - {}}}$",
                    "Постройте график функции $y = {}x + {}$ и найдите точки пересечения с осями координат",
                    "Найдите корни квадратного уравнения: ${}x^2 + {}x + {} = 0$"
                ],
                'subject': 'Математика',
                'answer_templates': [
                    "x = {}",
                    "Ответ: {}",
                    "$\\frac{{{}}}{{{}}}$",
                    "Точки пересечения: ({}, 0) и (0, {})",
                    "$x_1 = {}, x_2 = {}$"
                ]
            },
            # Физические задания  
            {
                'templates': [
                    "Автомобиль движется со скоростью {} м/с. Какой путь он пройдет за {} секунд?",
                    "Тело массой {} кг действует на опору с силой {} Н. Найдите ускорение свободного падения.",
                    "Определите плотность вещества, если масса тела {} г, а объем {} см³",
                    "При нагревании {} г воды от {}°C до {}°C затрачено {} Дж энергии. Найдите удельную теплоемкость воды.",
                    "Найдите количество теплоты, необходимое для плавления {} кг льда при температуре плавления"
                ],
                'subject': 'Физика', 
                'answer_templates': [
                    "s = {} м",
                    "g = {} м/с²", 
                    "ρ = {} г/см³",
                    "c = {} Дж/(кг·°C)",
                    "Q = {} кДж"
                ]
            }
        ]
        
        self.tasks = []
        tasks_count = self.size_config['tasks']
        successful_tasks = 0
        failed_tasks = 0
        
        for i in range(tasks_count):
            try:
                # ИСПРАВЛЕНО: Выбираем случайный предмет и шаблон
                subject_data = random.choice(task_templates)
                template = random.choice(subject_data['templates'])
                answer_template = random.choice(subject_data['answer_templates'])
                
                # Находим подходящие темы для данного предмета
                suitable_topics = [t for t in self.topics.values() 
                                if t.subject == subject_data['subject']]
                
                if not suitable_topics:
                    self.stdout.write(f"   ⚠️ Не найдено подходящих тем для предмета {subject_data['subject']}")
                    failed_tasks += 1
                    continue
                    
                topic = random.choice(suitable_topics)
                
                # Проверяем что тема корректно создана
                if not topic or not topic.pk:
                    self.stdout.write(f"   ⚠️ Некорректная тема: {topic}")
                    failed_tasks += 1
                    continue
                
                # Выбираем подтему (50% вероятность)
                subtopic = None
                if random.random() < 0.5:
                    subtopics = list(topic.subtopics.all())
                    if subtopics:
                        subtopic = random.choice(subtopics)
                
                # Генерируем числовые параметры для шаблона
                params = [random.randint(1, 20) for _ in range(template.count('{}'))]
                answer_params = [random.randint(1, 100) for _ in range(answer_template.count('{}'))]
                
                # Создаем текст и ответ
                try:
                    text = template.format(*params)
                    answer = answer_template.format(*answer_params)
                except IndexError:
                    # Fallback если параметров не хватает
                    text = template.replace('{}', str(random.randint(1, 10)))
                    answer = answer_template.replace('{}', str(random.randint(1, 100)))
                
                # Создаем задание
                task = Task.objects.create(
                    text=text,
                    answer=answer,
                    topic=topic,
                    subtopic=subtopic,
                    task_type=random.choice(['computational', 'qualitative', 'theoretical', 'practical', 'test']),
                    difficulty=random.randint(1, 5),
                    cognitive_level=random.choice(['remember', 'understand', 'apply', 'analyze', 'evaluate']),
                    estimated_time=random.randint(3, 15),
                    content_element=f"{random.randint(1,4)}.{random.randint(1,5)}",
                    requirement_element=f"{random.randint(1,3)}.{random.randint(1,4)}"
                )
                
                # ДОБАВЛЕНО: Проверяем что задание создалось корректно
                if task and task.pk and task.topic:
                    self.tasks.append(task)
                    successful_tasks += 1
                    
                    # Добавляем краткое и полное решение (30% вероятность)
                    if random.random() < 0.3:
                        task.short_solution = f"Применяем формулу и получаем {answer}"
                        task.full_solution = f"Подробное решение:\n1. Анализируем условие\n2. Применяем соответствующую формулу\n3. Вычисляем результат: {answer}"
                        task.save()
                    
                    # Добавляем подсказку (20% вероятность) 
                    if random.random() < 0.2:
                        task.hint = f"Вспомните основные формулы по теме '{topic.name}'"
                        task.save()
                else:
                    self.stdout.write(f"   ❌ Задание не создалось корректно")
                    failed_tasks += 1
                    
            except Exception as e:
                self.stdout.write(f"   ❌ Ошибка создания задания {i+1}: {e}")
                failed_tasks += 1
                continue
                
            if (successful_tasks + failed_tasks) % 100 == 0:
                self.stdout.write(f"   Обработано: {successful_tasks + failed_tasks}, успешно: {successful_tasks}")
        
        self.stdout.write(f"   ✅ Заданий создано успешно: {successful_tasks}")
        self.stdout.write(f"   ❌ Заданий с ошибками: {failed_tasks}")


    def create_task_groups(self):
        """Создание групп аналогичных заданий"""
        self.stdout.write("🔗 Создание групп аналогичных заданий...")
        
        # ДОБАВЛЕНО: Диагностика созданных заданий
        total_tasks = len(self.tasks)
        tasks_with_topics = len([t for t in self.tasks if t.topic])
        
        self.stdout.write(f"   Всего заданий создано: {total_tasks}")
        self.stdout.write(f"   Заданий с темами: {tasks_with_topics}")
        
        if tasks_with_topics == 0:
            self.stdout.write("   ⚠️ Ни у одного задания нет темы - пропускаем создание групп")
            self.analog_groups = []
            return
        
        # Группируем задания по темам
        tasks_by_topic = {}
        for task in self.tasks:
            # ИСПРАВЛЕНО: Проверяем что у задания есть тема
            if not task.topic:
                self.stdout.write(f"   ⚠️ Задание без темы: {task.text[:30]}...")
                continue
                
            topic_key = f"{task.topic.subject}_{task.topic.grade_level}_{task.topic.name}"
            if topic_key not in tasks_by_topic:
                tasks_by_topic[topic_key] = []
            tasks_by_topic[topic_key].append(task)
        
        self.stdout.write(f"   Тем с заданиями: {len(tasks_by_topic)}")
        
        self.analog_groups = []
        
        for topic_key, topic_tasks in tasks_by_topic.items():
            self.stdout.write(f"   Обрабатываем тему: {topic_key} ({len(topic_tasks)} заданий)")
            
            if len(topic_tasks) < 3:  # Пропускаем если мало заданий
                self.stdout.write(f"     Пропущена (мало заданий): {len(topic_tasks)} < 3")
                continue
            
            # Создаем 1-3 группы для темы
            groups_count = min(random.randint(1, 3), len(topic_tasks) // 3)
            self.stdout.write(f"     Создаем групп: {groups_count}")
            
            for group_num in range(groups_count):
                # ИСПРАВЛЕНО: Безопасное выделение заданий
                try:
                    # Выбираем количество заданий для группы
                    tasks_for_group = min(random.randint(3, 8), len(topic_tasks))
                    
                    if tasks_for_group > len(topic_tasks):
                        tasks_for_group = len(topic_tasks)
                    
                    # Выбираем случайные задания из темы
                    group_tasks = random.sample(topic_tasks, tasks_for_group)
                    
                    # ИСПРАВЛЕНО: Проверяем что группа не пустая
                    if not group_tasks:
                        self.stdout.write(f"       Пропущена пустая группа {group_num + 1}")
                        continue
                    
                    # Проверяем что у первого задания есть тема
                    if not group_tasks[0].topic:
                        self.stdout.write(f"       Пропущена группа {group_num + 1} - нет темы у заданий")
                        continue
                    
                    # Создаем группу аналогов
                    group_name = f"{topic_key.replace('_', ' ')} - Группа {group_num + 1}"
                    
                    # ИСПРАВЛЕНО: Безопасное создание описания
                    try:
                        description = f"Аналогичные задания по теме {group_tasks[0].topic.name}"
                    except AttributeError:
                        description = f"Аналогичные задания (группа {group_num + 1})"
                    
                    analog_group = AnalogGroup.objects.create(
                        name=group_name,
                        description=description
                    )
                    
                    # ИСПРАВЛЕНО: Создаем связи с проверками
                    relations_created = 0
                    for task in group_tasks:
                        try:
                            TaskGroup.objects.create(
                                task=task,
                                group=analog_group
                            )
                            relations_created += 1
                        except Exception as e:
                            self.stdout.write(f"         ❌ Ошибка связи задания {task.get_short_uuid()}: {e}")
                    
                    self.analog_groups.append(analog_group)
                    self.stdout.write(f"     ✅ Группа '{group_name}': {relations_created} заданий")
                    
                    # Удаляем использованные задания чтобы не дублировать
                    for task in group_tasks:
                        if task in topic_tasks:
                            topic_tasks.remove(task)
                            
                except Exception as e:
                    self.stdout.write(f"     ❌ Ошибка создания группы {group_num + 1}: {e}")
                    continue
        
        total_groups = len(self.analog_groups)
        self.stdout.write(f"   ✅ Создано групп аналогов: {total_groups}")

    def create_works(self):
        """Создание работ и вариантов"""
        self.stdout.write("📋 Создание работ и вариантов...")
        
        work_templates = [
            "Контрольная работа по теме '{}'",
            "Самостоятельная работа '{}'",
            "Диагностическая работа: {}",
            "Практическая работа '{}'",
            "Домашняя работа по {}",
        ]
        
        self.works = []
        works_count = self.size_config['works']
        
        for i in range(works_count):
            # Выбираем случайную тему
            topic = random.choice(list(self.topics.values()))
            work_name = random.choice(work_templates).format(topic.name)
            
            # Создаем работу
            work = Work.objects.create(
                name=work_name,
                work_type=random.choice(['test', 'quiz', 'exam', 'diagnostic', 'homework', 'practice']),
                duration=random.choice([45, 60, 90, 120]),
                variant_counter=0
            )
            
            # Находим подходящие группы аналогов для темы
            topic_groups = [ag for ag in self.analog_groups 
                           if topic.name in ag.name]
            
            if not topic_groups:
                continue
            
            # Добавляем 2-5 групп заданий в работу
            selected_groups = random.sample(topic_groups, min(random.randint(2, 5), len(topic_groups)))
            
            for analog_group in selected_groups:
                WorkAnalogGroup.objects.create(
                    work=work,
                    analog_group=analog_group,
                    count=random.randint(1, 2)  # 1-2 задания из группы
                )
            
            # Генерируем варианты (2-4 варианта)
            variants_count = random.randint(2, 4)
            work.generate_variants(variants_count)
            
            self.works.append(work)

    def create_students(self):
        """Создание учеников и классов"""
        self.stdout.write("👥 Создание учеников и классов...")
        
        # Имена для генерации
        first_names_m = ['Александр', 'Дмитрий', 'Максим', 'Артем', 'Иван', 'Михаил', 'Даниил', 'Егор', 'Андрей', 'Илья']
        first_names_f = ['Анастасия', 'Дарья', 'Мария', 'Полина', 'Анна', 'Екатерина', 'Алиса', 'Виктория', 'Елизавета', 'София']
        last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Волков', 'Соколов', 'Лебедев', 'Козлов']
        middle_names_m = ['Александрович', 'Дмитриевич', 'Максимович', 'Артемович', 'Иванович', 'Михайлович']
        middle_names_f = ['Александровна', 'Дмитриевна', 'Максимовна', 'Артемовна', 'Ивановна', 'Михайловна']
        
        # Создаем классы (7А, 7Б, 8А, 8Б, 9А, 9Б)
        classes = []
        for grade in [7, 8, 9]:
            for letter in ['А', 'Б']:
                class_name = f"{grade}{letter}"
                student_group = StudentGroup.objects.create(name=class_name)
                classes.append(student_group)
        
        # Создаем учеников
        students_count = self.size_config['students']
        students_per_class = students_count // len(classes)
        
        self.students = []
        
        for class_group in classes:
            for i in range(students_per_class):
                # Определяем пол случайно
                is_male = random.choice([True, False])
                
                first_name = random.choice(first_names_m if is_male else first_names_f)
                last_name = random.choice(last_names)
                
                # Склоняем фамилию для женского пола
                if not is_male and last_name.endswith('ов'):
                    last_name = last_name[:-2] + 'ова'
                elif not is_male and last_name.endswith('ин'):
                    last_name = last_name[:-2] + 'ина'
                
                middle_name = random.choice(middle_names_m if is_male else middle_names_f)
                
                # Email (30% учеников)
                email = ''
                if random.random() < 0.3:
                    email_name = f"{first_name.lower()}.{last_name.lower()}"
                    email = f"{email_name}@example.com"
                
                student = Student.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    email=email
                )
                
                # Добавляем в класс
                class_group.students.add(student)
                self.students.append(student)

    def create_courses(self):
        """Создание курсов и привязка работ (оптимизированная версия)"""
        self.stdout.write("📚 Создание курсов...")
        
        subjects = ['Математика', 'Физика']
        grades = [7, 8, 9]
        
        self.courses = []
        
        # ОПТИМИЗАЦИЯ: Предварительно загружаем все связи
        from django.db import connection
        
        for subject in subjects:
            for grade in grades:
                course_name = f"{subject} {grade} класс"
                
                course = Course.objects.create(
                    name=course_name,
                    subject=subject,
                    grade_level=grade,
                    academic_year='2024-2025',
                    description=f"Курс {subject.lower()} для {grade} класса",
                    start_date=datetime(2024, 9, 1).date(),
                    end_date=datetime(2025, 5, 31).date(),
                    total_hours=random.randint(60, 120),
                    hours_per_week=random.choice([2, 3, 4]),
                    is_active=True
                )
                
                # ОПТИМИЗИРОВАННЫЙ поиск подходящих работ
                suitable_works = Work.objects.filter(
                    workanaloggroup__analog_group__taskgroup__task__topic__subject=subject,
                    workanaloggroup__analog_group__taskgroup__task__topic__grade_level=grade
                ).distinct()
                
                suitable_works_list = list(suitable_works)
                self.stdout.write(f"   Найдено {len(suitable_works_list)} подходящих работ для {course_name}")
                
                # Добавляем работы в курс
                if suitable_works_list:
                    selected_works = random.sample(
                        suitable_works_list, 
                        min(random.randint(3, 8), len(suitable_works_list))
                    )
                    
                    for i, work in enumerate(selected_works, 1):
                        CourseAssignment.objects.create(
                            course=course,
                            work=work,
                            order=i,
                            planned_date=datetime(2024, 9, 1).date() + timedelta(weeks=i*2),
                            weight=random.uniform(0.8, 1.2)
                        )
                    
                    self.stdout.write(f"   Добавлено {len(selected_works)} работ в {course_name}")
                else:
                    self.stdout.write(f"   ⚠️ Не найдено подходящих работ для {course_name}")
                
                self.courses.append(course)

                
    def create_events(self):
        """Создание событий и участий"""
        self.stdout.write("📅 Создание событий...")
        
        self.events = []
        
        # Создаем события для каждого курса
        for course in self.courses:
            course_works = [ca.work for ca in course.courseassignment_set.all()]
            
            if not course_works:
                continue
            
            # Создаем 2-4 события на курс
            events_count = min(random.randint(2, 4), len(course_works))
            selected_works = random.sample(course_works, events_count)
            
            for i, work in enumerate(selected_works):
                # Дата события
                event_date = datetime(2024, 9, 15) + timedelta(weeks=i*3 + random.randint(0, 7))
                
                event = Event.objects.create(
                    name=f"{work.name} - {course.name}",
                    work=work,
                    course=course,
                    planned_date=event_date,
                    actual_start=event_date + timedelta(minutes=random.randint(-10, 30)),
                    status=random.choice(['completed', 'graded', 'reviewing']),
                    description=f"Проведение {work.get_work_type_display().lower()} для {course.name}",
                    location=f"Кабинет {random.randint(101, 350)}"
                )
                
                # Находим учеников подходящего класса
                suitable_students = [s for s in self.students 
                                   if any(sg.get_grade_level() == course.grade_level 
                                         for sg in s.studentgroup_set.all())]
                
                if not suitable_students:
                    continue
                
                # Добавляем участников (70-100% учеников класса)
                participants_count = int(len(suitable_students) * random.uniform(0.7, 1.0))
                participants = random.sample(suitable_students, participants_count)
                
                variants = list(work.variant_set.all())
                
                for student in participants:
                    # Статус участия
                    participation_status = random.choices(
                        ['completed', 'graded', 'absent'],
                        weights=[70, 25, 5]
                    )[0]
                    
                    # Временные метки
                    started_at = None
                    completed_at = None
                    graded_at = None
                    
                    if participation_status != 'absent':
                        started_at = event.actual_start + timedelta(minutes=random.randint(0, 15))
                        completed_at = started_at + timedelta(minutes=random.randint(30, work.duration))
                        
                        if participation_status == 'graded':
                            graded_at = completed_at + timedelta(days=random.randint(1, 7))
                    
                    participation = EventParticipation.objects.create(
                        event=event,
                        student=student,
                        variant=random.choice(variants) if variants else None,
                        status=participation_status,
                        started_at=started_at,
                        completed_at=completed_at,
                        graded_at=graded_at,
                        seat_number=f"{random.randint(1, 6)}-{random.randint(1, 8)}"
                    )
                    
                    # Создаем оценку (если проверено)
                    if participation_status == 'graded':
                        self.create_mark_for_participation(participation)
                
                self.events.append(event)

    def create_mark_for_participation(self, participation):
        """Создание оценки для участия"""
        # Генерируем реалистичную оценку
        score_weights = [5, 15, 35, 35, 10]  # 2, 3, 4, 5, отсутствует
        score = random.choices([2, 3, 4, 5, None], weights=score_weights)[0]
        
        max_points = random.randint(20, 50)
        
        if score:
            # Привязываем баллы к оценке
            if score == 5:
                points = random.randint(int(max_points * 0.85), max_points)
            elif score == 4:
                points = random.randint(int(max_points * 0.65), int(max_points * 0.84))
            elif score == 3:
                points = random.randint(int(max_points * 0.45), int(max_points * 0.64))
            else:  # score == 2
                points = random.randint(0, int(max_points * 0.44))
        else:
            points = None
        
        # Комментарии
        comments_pool = [
            "Хорошая работа, все задания выполнены верно.",
            "Есть вычислительные ошибки в задании 3.",
            "Необходимо повторить тему 'Квадратные уравнения'.",
            "Отличное понимание материала!",
            "Задание 2 выполнено неполно.",
            "Рекомендуется дополнительная подготовка.",
            "Творческий подход к решению задач.",
            "Нужно внимательнее читать условия задач."
        ]
        
        teacher_comment = random.choice(comments_pool) if random.random() < 0.6 else ""
        
        # Детализация по заданиям (для части оценок)
        task_scores = {}
        if participation.variant and random.random() < 0.4:
            variant_tasks = list(participation.variant.tasks.all())
            for j, task in enumerate(variant_tasks[:5], 1):  # Максимум 5 заданий
                task_max = random.randint(3, 8)
                task_points = random.randint(0, task_max)
                task_scores[str(task.id)] = {
                    'points': task_points,
                    'max_points': task_max,
                    'comment': random.choice(['Верно', 'Частично', 'Ошибка', '']) if random.random() < 0.3 else ''
                }
        
        Mark.objects.create(
            participation=participation,
            score=score,
            points=points,
            max_points=max_points,
            task_scores=task_scores,
            teacher_comment=teacher_comment,
            checked_at=participation.graded_at,
            checked_by=random.choice(['Иванова И.И.', 'Петрова П.П.', 'Сидорова С.С.']),
            is_excellent=score == 5 and random.random() < 0.1,
            needs_attention=score in [2, 3] and random.random() < 0.3
        )

    def create_reviews(self):
        """Создание данных для проверки"""
        self.stdout.write("✅ Создание данных проверки...")
        
        # Создаем пользователей-учителей
        teachers = []
        teacher_names = ['Иванова И.И.', 'Петрова П.П.', 'Сидорова С.С.', 'Козлова К.К.']
        
        for name in teacher_names:
            last_name, initials = name.split(' ')
            username = f"teacher_{last_name.lower()}"
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    first_name=initials[0],
                    last_name=last_name,
                    email=f"{username}@school.edu"
                )
                teachers.append(user)
        
        # Типовые комментарии
        comment_templates = [
            ('excellent', 'Превосходное решение! Все этапы выполнены безупречно.'),
            ('good', 'Хорошая работа, но есть незначительные недочеты.'),
            ('needs_improvement', 'Необходимо повторить правила решения квадратных уравнений.'),
            ('mistake', 'Типичная ошибка в знаках при раскрытии скобок.'),
            ('suggestion', 'Рекомендую использовать рациональный способ решения.'),
        ]
        
        for category, text in comment_templates:
            ReviewComment.objects.create(
                text=text,
                category=category,
                usage_count=random.randint(0, 50)
            )
        
        # Создаем сессии проверки
        for event in random.sample(self.events, min(10, len(self.events))):
            if teachers and event.status in ['graded', 'reviewing']:
                teacher = random.choice(teachers)
                
                total_participants = event.eventparticipation_set.count()
                checked_participants = event.eventparticipation_set.filter(status='graded').count()
                
                session = ReviewSession.objects.create(
                    reviewer=teacher,
                    event=event,
                    total_participations=total_participants,
                    checked_participations=checked_participants,
                    finished_at=timezone.now() if checked_participants == total_participants else None
                )
                
                if checked_participants > 0:
                    avg_time = timedelta(minutes=random.randint(3, 12))
                    session.average_time_per_work = avg_time
                    session.save()

    def export_to_json(self, filename):
        """Экспорт созданных данных в JSON"""
        self.stdout.write(f"📤 Экспорт данных в {filename}...")
        
        # Простой экспорт структуры (можно расширить)
        export_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'size': self.size_config,
                'total_records': {
                    'students': Student.objects.count(),
                    'tasks': Task.objects.count(),
                    'works': Work.objects.count(),
                    'events': Event.objects.count(),
                    'marks': Mark.objects.count(),
                }
            },
            'summary': {
                'subjects': list(set(t.subject for t in Topic.objects.all())),
                'grades': list(set(t.grade_level for t in Topic.objects.all())),
                'task_types': list(set(t.task_type for t in Task.objects.all())),
                'work_types': list(set(w.work_type for w in Work.objects.all())),
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(f"✅ Экспорт завершен: {filename}")
