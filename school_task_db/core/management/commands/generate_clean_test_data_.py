from django.core.management.base import BaseCommand
from django.db import transaction
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Генерация чистых тестовых данных без багов'

    def add_arguments(self, parser):
        parser.add_argument('--topics', type=int, default=15, help='Количество тем')
        parser.add_argument('--tasks', type=int, default=40, help='Количество заданий')
        parser.add_argument('--students', type=int, default=25, help='Количество учеников')

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('🧹 Очистка старых данных...')
            self.clear_data()
            
            self.stdout.write('📚 Создание тем и подтем...')
            topics = self.create_topics(options['topics'])
            
            self.stdout.write('📝 Создание заданий...')
            tasks = self.create_tasks(options['tasks'], topics)
            
            self.stdout.write('👥 Создание учеников...')
            students = self.create_students(options['students'])
            
            self.stdout.write('🎯 Создание групп и работ...')
            self.create_groups_and_works(tasks)

        self.stdout.write(
            self.style.SUCCESS(f'✅ Создано: {len(topics)} тем, {len(tasks)} заданий, {len(students)} учеников')
        )

    def clear_data(self):
        """Очистка данных кроме справочников и пользователей"""
        from tasks.models import Task, TaskImage
        from curriculum.models import Topic, SubTopic, Course
        from students.models import Student, StudentGroup
        from task_groups.models import AnalogGroup, TaskGroup
        from works.models import Work, WorkAnalogGroup, Variant
        from events.models import Event, EventParticipation, Mark
        
        # Очищаем в правильном порядке (по зависимостям)
        Mark.objects.all().delete()
        EventParticipation.objects.all().delete()
        Event.objects.all().delete()
        Variant.objects.all().delete()
        WorkAnalogGroup.objects.all().delete()
        Work.objects.all().delete()
        TaskGroup.objects.all().delete()
        AnalogGroup.objects.all().delete()
        TaskImage.objects.all().delete()
        Task.objects.all().delete()
        SubTopic.objects.all().delete()
        Topic.objects.all().delete()
        Course.objects.all().delete()
        
        # ПРАВИЛЬНАЯ очистка ManyToMany связей
        for group in StudentGroup.objects.all():
            group.students.clear()  # Очищаем связи M2M
        
        Student.objects.all().delete()
        StudentGroup.objects.all().delete()


    def create_topics(self, count):
        """Создание тем с подтемами"""
        from curriculum.models import Topic, SubTopic
        
        # Используем предметы из справочника
        try:
            from references.helpers import get_reference_choices
            subject_choices = get_reference_choices('subjects')
            subjects = [choice[0] for choice in subject_choices] if subject_choices else []
        except:
            subjects = []
        
        if not subjects:
            # Fallback если справочники не работают
            subjects = ['mathematics', 'algebra', 'geometry', 'physics', 'chemistry']
        
        sections = {
            'mathematics': ['Арифметика', 'Алгебра', 'Геометрия', 'Функции'],
            'algebra': ['Выражения', 'Уравнения', 'Неравенства', 'Функции'],
            'geometry': ['Планиметрия', 'Стереометрия', 'Векторы'],
            'physics': ['Механика', 'Термодинамика', 'Электричество'],
            'chemistry': ['Органическая химия', 'Неорганическая химия'],
            'russian': ['Фонетика', 'Морфология', 'Синтаксис'],
            'history': ['Древний мир', 'Средние века', 'Новое время'],
            'biology': ['Ботаника', 'Зоология', 'Анатомия']
        }
        
        topics = []
        
        for i in range(count):
            subject = random.choice(subjects)
            section_list = sections.get(subject, ['Раздел 1', 'Раздел 2', 'Раздел 3'])
            section = random.choice(section_list)
            grade = random.choice([7, 8, 9, 10, 11])
            
            topic = Topic.objects.create(
                name=f"Тема {i+1}: {section}",
                subject=subject,
                section=section,
                grade_level=grade,
                order=i+1,
                description=f"Описание темы по {section} для {grade} класса",
                difficulty_level=random.choice([1, 2, 3])
            )
            topics.append(topic)
            
            # Создаем 2-4 подтемы для каждой темы
            subtopic_count = random.randint(2, 4)
            for j in range(subtopic_count):
                SubTopic.objects.create(
                    topic=topic,
                    name=f"Подтема {j+1}: Часть {j+1}",
                    description=f"Подтема {j+1} по теме {topic.name}",
                    order=j+1
                )
        
        return topics

    def create_tasks(self, count, topics):
        """Создание заданий с правильными типами данных"""
        from tasks.models import Task
        
        # Получаем значения из справочников (используем как подсказки)
        try:
            from references.helpers import (
                get_task_type_choices, 
                get_difficulty_choices,
                get_cognitive_level_choices
            )
            
            # Пробуем справочники
            task_type_choices = get_task_type_choices()
            difficulty_choices = get_difficulty_choices()
            cognitive_choices = get_cognitive_level_choices()
            
            task_types = [choice[0] for choice in task_type_choices] if task_type_choices else []
            difficulties_from_ref = [choice[0] for choice in difficulty_choices] if difficulty_choices else []
            cognitive_levels = [choice[0] for choice in cognitive_choices] if cognitive_choices else []
        except:
            task_types = []
            difficulties_from_ref = []
            cognitive_levels = []


        # Fallback на статические choices из модели
        if not task_types:
            task_types = [choice[0] for choice in Task.TASK_TYPES]
        
        # ИСПРАВЛЯЕМ ЛОГИКУ ДЛЯ DIFFICULTY: всегда используем числа
        if difficulties_from_ref:
            # УМНАЯ ПРОВЕРКА: числа или строки в справочнике?
            try:
                # Пытаемся преобразовать первый элемент в число
                test_value = int(difficulties_from_ref[0])
                # Если получилось - преобразуем все элементы в числа
                difficulties = [int(d) for d in difficulties_from_ref]
                self.stdout.write(f'📊 Используем числовые уровни сложности из справочника: {difficulties}')
            except (ValueError, TypeError):
                # Если в справочнике строки - используем статические числа из модели
                difficulties = [choice[0] for choice in Task.DIFFICULTY_LEVELS]
                self.stdout.write(f'📊 Справочник содержит строки, используем числа из модели: {difficulties}')
        else:
            # Нет справочника - используем статические числа
            difficulties = [choice[0] for choice in Task.DIFFICULTY_LEVELS]
            self.stdout.write(f'📊 Справочник пустой, используем числа из модели: {difficulties}')
        
        if not cognitive_levels:
            cognitive_levels = ['remember', 'understand', 'apply', 'analyze']


        # Используем предметы из справочника для генерации тем
        try:
            from references.helpers import get_reference_choices
            subject_choices = get_reference_choices('subjects')
            subjects = [choice[0] for choice in subject_choices] if subject_choices else []
        except:
            subjects = []


        if not subjects:
            # Fallback на базовые предметы
            subjects = ['mathematics', 'algebra', 'geometry', 'physics', 'chemistry']
        
        tasks = []
        
        for i in range(count):
            topic = random.choice(topics)
            
            # 70% заданий с подтемой, 30% без
            subtopic = None
            if random.random() < 0.7:
                subtopics = list(topic.subtopics.all())
                if subtopics:
                    subtopic = random.choice(subtopics)
            
            # Правильные типы данных
            task_type = random.choice(task_types)
            difficulty = random.choice(difficulties)  # ВСЕГДА ЧИСЛО!
            cognitive_level = random.choice(cognitive_levels)
            
            # ОТЛАДОЧНЫЙ ВЫВОД для первых 3 заданий
            if i < 3:
                self.stdout.write(f'🔍 Задание {i+1}: difficulty={difficulty} (тип: {type(difficulty)})')
            
            task = Task.objects.create(
                text=f"Задание {i+1}: Решите задачу по теме {topic.name}. "
                    f"Найдите значение выражения или решите уравнение. "
                    f"Подробно опишите ход решения.",
                answer=f"Ответ к заданию {i+1}",
                short_solution=f"Краткое решение задания {i+1}",
                full_solution=f"Подробное решение задания {i+1} с пояснениями",
                hint=f"Подсказка для задания {i+1}",
                topic=topic,
                subtopic=subtopic,
                task_type=task_type,
                difficulty=difficulty,  # ЧИСЛО!
                cognitive_level=cognitive_level,
                content_element=f"{random.randint(1,5)}.{random.randint(1,9)}",
                requirement_element=f"{random.randint(1,3)}.{random.randint(1,9)}",
                estimated_time=random.choice([5, 10, 15, 20, 30, 45])
            )
            tasks.append(task)
        
        return tasks

    def create_students(self, count):
        """Создание учеников"""
        from students.models import Student, StudentGroup
        
        # Создаем группы (классы)
        groups = []
        for grade in [7, 8, 9, 10, 11]:
            for letter in ['А', 'Б']:
                group = StudentGroup.objects.create(
                    name=f"{grade}{letter}"
                )
                groups.append(group)
                self.stdout.write(f'✅ Создан класс: {group.name}')
        
        # Создаем учеников
        first_names = [
            'Александр', 'Мария', 'Дмитрий', 'Анна', 'Максим', 'Екатерина',
            'Андрей', 'Ольга', 'Никита', 'Татьяна', 'Артем', 'Елена',
            'Сергей', 'Наталья', 'Алексей', 'Ирина', 'Владимир', 'Светлана'
        ]
        last_names = [
            'Иванов', 'Петров', 'Сидоров', 'Козлов', 'Новиков', 'Морозов',
            'Петрова', 'Иванова', 'Федорова', 'Михайлова', 'Соколова', 'Яковлева',
            'Смирнов', 'Кузнецов', 'Попов', 'Васильев'
        ]
        
        students = []
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            middle_name = random.choice(['Александрович', 'Сергеевич', 'Дмитриевич']) if i % 2 == 0 else random.choice(['Александровна', 'Сергеевна', 'Дмитриевна'])
            
            student = Student.objects.create(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                email=f"{first_name.lower()}.{last_name.lower()}{i+1}@school.edu"
            )
            
            # Добавляем в случайную группу
            group = random.choice(groups)
            group.students.add(student)
            
            students.append(student)
            
            # Отладочный вывод для первых 3 учеников
            if i < 3:
                self.stdout.write(f'👤 Создан ученик: {student.get_full_name()} → класс {group.name}')
        
        # Статистика по классам
        for group in groups:
            count = group.students.count()
            self.stdout.write(f'📊 Класс {group.name}: {count} учеников')
        
        return students


    def create_groups_and_works(self, tasks):
        """Создание групп аналогов и работ"""
        from task_groups.models import AnalogGroup, TaskGroup
        from works.models import Work, WorkAnalogGroup
        
        # Создаем группы аналогов
        groups = []
        for i in range(5):
            group = AnalogGroup.objects.create(
                name=f"Группа аналогов {i+1}",
                description=f"Описание группы {i+1}"
            )
            
            # Добавляем 3-5 заданий в группу
            group_tasks = random.sample(tasks, min(random.randint(3, 5), len(tasks)))
            for task in group_tasks:
                TaskGroup.objects.create(task=task, group=group)
            
            groups.append(group)
        
        # Создаем работы
        try:
            from references.helpers import get_work_type_choices
            work_type_choices = get_work_type_choices()
            work_types = [choice[0] for choice in work_type_choices] if work_type_choices else []
        except:
            work_types = []
        
        if not work_types:
            work_types = ['test', 'quiz', 'exam']
        
        for i in range(3):
            work = Work.objects.create(
                name=f"Контрольная работа {i+1}",
                duration=45,
                work_type=random.choice(work_types)
            )
            
            # Добавляем 2 случайные группы в работу
            selected_groups = random.sample(groups, min(2, len(groups)))
            for j, group in enumerate(selected_groups):
                WorkAnalogGroup.objects.create(
                    work=work,
                    analog_group=group,
                    count=random.randint(1, 2)
                )
            
            # Генерируем варианты
            try:
                work.generate_variants(4)
            except Exception as e:
                self.stdout.write(f'⚠️ Ошибка генерации вариантов для {work.name}: {e}')
