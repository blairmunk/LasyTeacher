"""
Создание масштабных тестовых данных для school_task_db.
python manage.py seed_large_test_data [--clear] [--size small|medium|large]
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone as tz
from django.db import transaction

from curriculum.models import Topic, SubTopic, Course, CourseAssignment
from tasks.models import Task
from task_groups.models import AnalogGroup, TaskGroup
from students.models import Student, StudentGroup, StudentTaskLog
from works.models import Work, WorkAnalogGroup, Variant, VariantTask
from events.models import Event, EventParticipation, Mark

SIZES = {
    'small': {'courses': 2, 'groups_per_topic': 2, 'tasks_per_group': 5, 'students_per_class': 10, 'classes_per_grade': 1, 'works_per_course': 3, 'variants': 2},
    'medium': {'courses': 4, 'groups_per_topic': 4, 'tasks_per_group': 15, 'students_per_class': 25, 'classes_per_grade': 2, 'works_per_course': 6, 'variants': 4},
    'large': {'courses': 8, 'groups_per_topic': 6, 'tasks_per_group': 30, 'students_per_class': 30, 'classes_per_grade': 3, 'works_per_course': 10, 'variants': 6},
}

SUBJECTS = [
    ('Математика', [
        ('Алгебраические выражения', 'Алгебра'),
        ('Линейные уравнения', 'Алгебра'),
        ('Функции', 'Алгебра'),
        ('Квадратные корни', 'Алгебра'),
        ('Квадратные уравнения', 'Алгебра'),
        ('Треугольники', 'Геометрия'),
        ('Четырехугольники', 'Геометрия'),
        ('Площадь', 'Геометрия')
    ]),
    ('Физика', [
        ('Механическое движение', 'Механика'),
        ('Взаимодействие тел', 'Механика'),
        ('Давление твердых тел', 'Механика'),
        ('Тепловые явления', 'Термодинамика'),
        ('Изменения агрегатных состояний', 'Термодинамика'),
        ('Электрические явления', 'Электродинамика'),
        ('Оптика', 'Оптика')
    ])
]

NAMES_M = ['Александр', 'Дмитрий', 'Максим', 'Артем', 'Иван', 'Михаил', 'Даниил', 'Егор']
NAMES_F = ['Анастасия', 'Дарья', 'Мария', 'Полина', 'Анна', 'Екатерина', 'Алиса', 'Виктория']
SURNAMES = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Волков', 'Соколов', 'Лебедев']
MID_M = ['Александрович', 'Дмитриевич', 'Максимович', 'Артемович', 'Иванович']
MID_F = ['Александровна', 'Дмитриевна', 'Максимовна', 'Артемовна', 'Ивановна']

class Command(BaseCommand):
    help = 'Создаёт масштабный набор тестовых данных'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Удалить все данные перед созданием')
        parser.add_argument('--size', choices=['small', 'medium', 'large'], default='medium', help='Размер данных')

    def handle(self, *args, **options):
        self.size_config = SIZES[options['size']]
        
        if options['clear']:
            self._clear()

        self.stdout.write(f'\n🚀 Создание тестовых данных (размер: {options["size"]})...\n')

        with transaction.atomic():
            ay = self._get_or_create_academic_year()
            topics = self._create_curriculum()
            tasks_by_group = self._create_tasks_and_groups(topics)
            classes_by_grade = self._create_students(ay)
            courses = self._create_courses(ay, classes_by_grade, tasks_by_group)
            self._create_events_and_marks(courses)

            self._print_summary()
            self.stdout.write(self.style.SUCCESS('\n✅ Тестовые данные успешно созданы!\n'))

    def _clear(self):
        self.stdout.write('🗑️  Очистка базы данных...')
        Mark.objects.all().delete()
        EventParticipation.objects.all().delete()
        Event.objects.all().delete()
        StudentTaskLog.objects.all().delete()
        VariantTask.objects.all().delete()
        Variant.objects.all().delete()
        CourseAssignment.objects.all().delete()
        WorkAnalogGroup.objects.all().delete()
        Work.objects.all().delete()
        TaskGroup.objects.all().delete()
        AnalogGroup.objects.all().delete()
        Task.objects.all().delete()
        Course.objects.all().delete()
        SubTopic.objects.all().delete()
        Topic.objects.all().delete()
        StudentGroup.objects.all().delete()
        Student.objects.all().delete()
        self.stdout.write('  Готово.\n')

    def _get_or_create_academic_year(self):
        try:
            from core.models import AcademicYear
            ay, _ = AcademicYear.objects.get_or_create(
                name='2024-2025',
                defaults={'start_date': date(2024, 9, 1), 'end_date': date(2025, 5, 31), 'is_active': True}
            )
            return ay
        except ImportError:
            return None

    def _create_curriculum(self):
        self.stdout.write('📚 Создание тем...')
        topics = []
        for grade in [7, 8, 9]:
            for subject, sub_topics_list in SUBJECTS:
                for i, (name, section) in enumerate(sub_topics_list, 1):
                    t = Topic.objects.create(
                        name=name, subject=subject, section=section, grade_level=grade,
                        order=i, description=f'Изучение {name} в {grade} классе'
                    )
                    SubTopic.objects.create(topic=t, name=f'{name}: теория', order=1)
                    SubTopic.objects.create(topic=t, name=f'{name}: практика', order=2)
                    topics.append(t)
        return topics

    def _create_tasks_and_groups(self, topics):
        self.stdout.write('📝 Создание заданий и групп аналогов...')
        tasks_by_group = []
        
        all_tasks = []
        all_groups = []
        all_task_group_links = []
        
        for topic in topics:
            for i in range(self.size_config['groups_per_topic']):
                group_diff = random.randint(1, 5)
                group = AnalogGroup.objects.create(name=f'{topic.name} - Группа {i+1}', difficulty=group_diff)
                all_groups.append(group)
                
                group_tasks = []
                for j in range(self.size_config['tasks_per_group']):
                    text = f"Тестовое задание №{j+1} по теме '{topic.name}' (Сложность: {group_diff})"
                    answer = f"Ответ {j+1}"
                    
                    task = Task(
                        text=text, answer=answer, difficulty=group_diff, 
                        task_type=random.choice(['computational', 'qualitative', 'test']),
                        topic=topic, cognitive_level='apply' if group_diff <= 2 else 'analyze'
                    )
                    all_tasks.append(task)
                    group_tasks.append(task)
                
                tasks_by_group.append((group, group_tasks))
        
        Task.objects.bulk_create(all_tasks)
        
        # After bulk create, tasks have IDs, create TaskGroup links
        # We need to iterate over all_tasks. Let's just create them one by one or fetch by text if needed.
        # Wait, bulk_create for Postgres returns IDs. SQLite might not. So we fetch them.
        all_tasks_saved = list(Task.objects.all())
        task_idx = 0
        for group, group_tasks in tasks_by_group:
            for _ in group_tasks:
                all_task_group_links.append(TaskGroup(task=all_tasks_saved[task_idx], group=group))
                task_idx += 1
                
        TaskGroup.objects.bulk_create(all_task_group_links)
        
        # update tasks_by_group with saved tasks
        saved_tasks_by_group = []
        task_idx = 0
        for group, group_tasks in tasks_by_group:
            saved_group_tasks = []
            for _ in group_tasks:
                saved_group_tasks.append(all_tasks_saved[task_idx])
                task_idx += 1
            saved_tasks_by_group.append((group, saved_group_tasks))

        return saved_tasks_by_group

    def _create_students(self, ay):
        self.stdout.write('👨‍🎓 Создание учеников и классов...')
        classes_by_grade = {7: [], 8: [], 9: []}
        
        letters = ['А', 'Б', 'В', 'Г', 'Д']
        
        all_students = []
        
        for grade in [7, 8, 9]:
            for i in range(self.size_config['classes_per_grade']):
                sg_kwargs = {'name': f'{grade}{letters[i]}'}
                if ay: sg_kwargs['academic_year'] = ay
                sg = StudentGroup.objects.create(**sg_kwargs)
                classes_by_grade[grade].append(sg)
                
                class_students = []
                for _ in range(self.size_config['students_per_class']):
                    is_m = random.choice([True, False])
                    first = random.choice(NAMES_M if is_m else NAMES_F)
                    mid = random.choice(MID_M if is_m else MID_F)
                    last = random.choice(SURNAMES)
                    if not is_m and last.endswith('ов'): last = last[:-2] + 'ова'
                    
                    student = Student(first_name=first, last_name=last, middle_name=mid)
                    all_students.append(student)
                    class_students.append(student)
                
                Student.objects.bulk_create(class_students)
                # re-fetch
                saved_students = Student.objects.filter(last_name__in=[s.last_name for s in class_students])
                sg.students.set(saved_students)

        return classes_by_grade

    def _create_courses(self, ay, classes_by_grade, tasks_by_group):
        self.stdout.write('📖 Создание курсов и работ...')
        courses = []
        
        start_date = date(2024, 9, 2)
        
        for grade in [7, 8, 9]:
            for subject, _ in SUBJECTS:
                if len(courses) >= self.size_config['courses']:
                    break
                    
                course_kwargs = {
                    'name': f'{subject} {grade} класс',
                    'subject': subject, 'grade_level': grade,
                    'hours_per_week': 3, 'is_active': True,
                    'start_date': start_date, 'end_date': date(2025, 5, 30),
                }
                if ay: course_kwargs['academic_year'] = ay
                course = Course.objects.create(**course_kwargs)
                course.student_groups.set(classes_by_grade[grade])
                courses.append(course)
                
                # Фильтруем группы аналогов для этого предмета и класса
                relevant_groups = [g for g, t in tasks_by_group if t and t[0].topic.subject == subject and t[0].topic.grade_level == grade]
                
                if not relevant_groups:
                    continue
                    
                # Создаем работы для курса
                for w_idx in range(self.size_config['works_per_course']):
                    work_groups = random.sample(relevant_groups, min(random.randint(3, 6), len(relevant_groups)))
                    
                    work = Work.objects.create(
                        name=f'Контрольная работа №{w_idx+1} по {subject} ({grade} класс)',
                        work_type=random.choice(['test', 'quiz', 'diagnostic']),
                        duration=45,
                    )
                    
                    for order, ag in enumerate(work_groups, 1):
                        WorkAnalogGroup.objects.create(work=work, analog_group=ag, count=1, order=order, weight=random.choice([1, 2]))
                    
                    planned_date = start_date + timedelta(weeks=(w_idx + 1) * 3)
                    CourseAssignment.objects.create(course=course, work=work, order=w_idx+1, planned_date=planned_date)
                    
                    # Генерируем варианты
                    work.compose_variants(self.size_config['variants'])

        return courses

    def _create_events_and_marks(self, courses):
        self.stdout.write('📊 Создание событий и оценок...')
        
        for course in courses:
            assignments = course.courseassignment_set.select_related('work').all()
            for ca in assignments:
                work = ca.work
                
                # Создаем событие
                event = Event.objects.create(
                    name=f'{work.name} - {course.name}',
                    work=work, course=course,
                    planned_date=ca.planned_date, actual_start=ca.planned_date,
                    status='graded'
                )
                
                variants = list(work.variant_set.prefetch_related('varianttask_set__task').all())
                if not variants: continue
                
                students = Student.objects.filter(studentgroup__courses=course).distinct()
                
                for i, student in enumerate(students):
                    variant = variants[i % len(variants)]
                    ep = EventParticipation.objects.create(
                        event=event, student=student, variant=variant, status='graded'
                    )
                    
                    total_pts = 0
                    total_max = 0
                    task_scores = {}
                    
                    for vt in variant.varianttask_set.all():
                        max_pts = int(vt.max_points)
                        pts = random.randint(int(max_pts * 0.3), max_pts)
                        task_scores[str(vt.task.pk)] = {'points': pts, 'max_points': max_pts, 'comment': ''}
                        total_pts += pts
                        total_max += max_pts
                        
                        # Добавляем StudentTaskLog
                        StudentTaskLog.objects.create(
                            student=student, task=vt.task,
                            difficulty=vt.task.difficulty or 2,
                            percentage=round((pts / max_pts * 100) if max_pts else 0, 1),
                            points=Decimal(str(pts)), max_points=Decimal(str(max_pts)),
                            is_correct=(pts == max_pts), completed_at=tz.now()
                        )
                        
                    pct = total_pts / total_max * 100 if total_max else 0
                    score = 5 if pct >= 85 else 4 if pct >= 65 else 3 if pct >= 40 else 2
                    
                    Mark.objects.create(
                        participation=ep, score=score, points=total_pts, max_points=total_max, task_scores=task_scores
                    )

    def _print_summary(self):
        self.stdout.write('\n' + '='*50)
        self.stdout.write('  СВОДКА МАСШТАБНЫХ ТЕСТОВЫХ ДАННЫХ')
        self.stdout.write('='*50)
        self.stdout.write(f'  Тем:            {Topic.objects.count()}')
        self.stdout.write(f'  Заданий:        {Task.objects.count()}')
        self.stdout.write(f'  Групп аналогов: {AnalogGroup.objects.count()}')
        self.stdout.write(f'  Классов:        {StudentGroup.objects.count()}')
        self.stdout.write(f'  Учеников:       {Student.objects.count()}')
        self.stdout.write(f'  Курсов:         {Course.objects.count()}')
        self.stdout.write(f'  Работ:          {Work.objects.count()}')
        self.stdout.write(f'  Вариантов:      {Variant.objects.count()}')
        self.stdout.write(f'  Событий:        {Event.objects.count()}')
        self.stdout.write(f'  Оценок:         {Mark.objects.count()}')
        self.stdout.write(f'  Логов заданий:  {StudentTaskLog.objects.count()}')
        self.stdout.write('='*50)
