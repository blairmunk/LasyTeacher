"""
Генерация тестовых данных для демонстрации heatmap.

Создаёт:
- 2 класса (9А, 9Б)
- 30 учеников
- ~60 заданий по физике (привязаны к темам)
- 3 работы с вариантами
- 5 событий (проведённые, с оценками)

Использование:
    python manage.py load_test_data
    python manage.py load_test_data --clear
"""

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from curriculum.models import Topic, SubTopic
from students.models import Student, StudentGroup
from tasks.models import Task
from task_groups.models import TaskGroup
from works.models import Work, Variant
from events.models import Event, EventParticipation, Mark


# === Имена ===

LAST_NAMES_M = [
    'Иванов', 'Петров', 'Сидоров', 'Козлов', 'Новиков',
    'Морозов', 'Волков', 'Соколов', 'Лебедев', 'Кузнецов',
    'Попов', 'Егоров', 'Фёдоров', 'Орлов', 'Андреев',
]

LAST_NAMES_F = [
    'Иванова', 'Петрова', 'Сидорова', 'Козлова', 'Новикова',
    'Морозова', 'Волкова', 'Соколова', 'Лебедева', 'Кузнецова',
]

FIRST_NAMES_M = [
    'Александр', 'Дмитрий', 'Максим', 'Артём', 'Иван',
    'Кирилл', 'Михаил', 'Даниил', 'Егор', 'Андрей',
    'Никита', 'Илья', 'Алексей', 'Матвей', 'Тимофей',
]

FIRST_NAMES_F = [
    'Анна', 'Мария', 'Елизавета', 'Виктория', 'Полина',
    'Алиса', 'Дарья', 'Софья', 'Ксения', 'Василиса',
]

MIDDLE_NAMES_M = [
    'Александрович', 'Дмитриевич', 'Сергеевич', 'Андреевич',
    'Иванович', 'Михайлович', 'Николаевич', 'Петрович',
]

MIDDLE_NAMES_F = [
    'Александровна', 'Дмитриевна', 'Сергеевна', 'Андреевна',
    'Ивановна', 'Михайловна', 'Николаевна', 'Петровна',
]


class Command(BaseCommand):
    help = 'Генерация тестовых данных (ученики, задания, работы, события, оценки)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все тестовые данные перед генерацией',
        )

    def handle(self, *args, **options):
        if options['clear']:
            from curriculum.models import Course, CourseAssignment
            CourseAssignment.objects.all().delete()
            Course.objects.all().delete()
            Mark.objects.all().delete()
            EventParticipation.objects.all().delete()
            Event.objects.all().delete()
            Variant.objects.all().delete()
            Work.objects.all().delete()
            TaskGroup.objects.all().delete()
            Task.objects.all().delete()
            Student.objects.all().delete()
            StudentGroup.objects.all().delete()
            self.stdout.write(self.style.WARNING('🗑  Все данные удалены'))

        with transaction.atomic():
            groups = self._create_groups()
            students = self._create_students(groups)
            tasks = self._create_tasks()
            works = self._create_works(tasks)
            course = self._create_course(works, groups)
            self._create_events(works, students, groups)

        self.stdout.write(self.style.SUCCESS('\n🎉 Тестовые данные загружены!'))


    def _create_groups(self):
        groups = {}
        for name in ['9А', '9Б']:
            group, _ = StudentGroup.objects.get_or_create(name=name)
            groups[name] = group
        self.stdout.write(f'👥 Классы: {len(groups)}')
        return groups

    def _create_students(self, groups):
        students = {'9А': [], '9Б': []}

        # 9А — первая половина имён
        group_a = groups['9А']
        for i in range(10):
            ln = LAST_NAMES_M[i]
            fn = FIRST_NAMES_M[i]
            mn = MIDDLE_NAMES_M[i % len(MIDDLE_NAMES_M)]
            student, _ = Student.objects.get_or_create(
                last_name=ln, first_name=fn,
                defaults={'middle_name': mn}
            )
            group_a.students.add(student)
            students['9А'].append(student)

        for i in range(5):
            ln = LAST_NAMES_F[i]
            fn = FIRST_NAMES_F[i]
            mn = MIDDLE_NAMES_F[i % len(MIDDLE_NAMES_F)]
            student, _ = Student.objects.get_or_create(
                last_name=ln, first_name=fn,
                defaults={'middle_name': mn}
            )
            group_a.students.add(student)
            students['9А'].append(student)

        # 9Б — вторая половина + изменённые имена
        group_b = groups['9Б']
        for i in range(10):
            ln = LAST_NAMES_M[14 - i]  # Обратный порядок
            fn = FIRST_NAMES_M[(i + 5) % len(FIRST_NAMES_M)]  # Сдвиг
            mn = MIDDLE_NAMES_M[(i + 3) % len(MIDDLE_NAMES_M)]
            student, _ = Student.objects.get_or_create(
                last_name=ln, first_name=fn,
                defaults={'middle_name': mn}
            )
            group_b.students.add(student)
            students['9Б'].append(student)

        for i in range(5):
            ln = LAST_NAMES_F[9 - i]  # Обратный порядок
            fn = FIRST_NAMES_F[(i + 3) % len(FIRST_NAMES_F)]  # Сдвиг
            mn = MIDDLE_NAMES_F[(i + 2) % len(MIDDLE_NAMES_F)]
            student, _ = Student.objects.get_or_create(
                last_name=ln, first_name=fn,
                defaults={'middle_name': mn}
            )
            group_b.students.add(student)
            students['9Б'].append(student)

        total = sum(len(v) for v in students.values())
        self.stdout.write(f'🧑‍🎓 Учеников: {total}')
        return students


    def _create_tasks(self):
        topics = Topic.objects.filter(
            subject='Физика', grade_level__in=[7, 8, 9]
        ).prefetch_related('subtopics')

        if not topics.exists():
            self.stdout.write(self.style.ERROR(
                'Нет физических тем! Сначала: python manage.py load_physics_topics'
            ))
            return []

        tasks = []
        task_types = ['qualitative', 'computational', 'test', 'theoretical']

        for topic in topics:
            subtopics = list(topic.subtopics.all())
            if not subtopics:
                continue

            for subtopic in subtopics:
                num_tasks = random.randint(2, 4)
                for j in range(num_tasks):
                    difficulty = random.choice([1, 1, 2, 2, 3])
                    task_type = random.choice(task_types)

                    task, created = Task.objects.get_or_create(
                        text=f'Задание по теме «{subtopic.name}» (вариант {j + 1}).\n'
                             f'Раздел: {topic.section} → {topic.name}.',
                        topic=topic,
                        subtopic=subtopic,
                        defaults={
                            'answer': f'Ответ к заданию {j + 1} по {subtopic.name}',
                            'difficulty': difficulty,
                            'task_type': task_type,
                            'cognitive_level': random.choice([
                                'remember', 'understand', 'apply', 'analyze',
                            ]),
                            'estimated_time': random.choice([3, 5, 5, 8, 10]),
                        }
                    )
                    if created:
                        tasks.append(task)

        self.stdout.write(f'📝 Заданий: {len(tasks)}')
        return tasks

    def _create_works(self, tasks):
        if not tasks:
            return []

        works_config = [
            {
                'name': 'КР №1: Механическое движение',
                'work_type': 'control',
                'topic_names': ['Механическое движение', 'Равноускоренное движение'],
                'tasks_per_variant': 8,
                'num_variants': 2,
            },
            {
                'name': 'СР: Силы в природе',
                'work_type': 'independent',
                'topic_names': ['Силы в природе', 'Законы Ньютона'],
                'tasks_per_variant': 5,
                'num_variants': 2,
            },
            {
                'name': 'КР №2: Тепловые явления',
                'work_type': 'control',
                'topic_names': [
                    'Внутренняя энергия и теплопередача',
                    'Количество теплоты',
                    'Изменения агрегатных состояний',
                ],
                'tasks_per_variant': 8,
                'num_variants': 2,
            },
        ]

        works = []

        for config in works_config:
            available = list(
                Task.objects.filter(
                    topic__name__in=config['topic_names'],
                ).order_by('?')
            )

            if len(available) < config['tasks_per_variant']:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️  {config["name"]}: мало заданий '
                    f'({len(available)} < {config["tasks_per_variant"]})'
                ))
                continue

            work, created = Work.objects.get_or_create(
                name=config['name'],
                defaults={
                    'work_type': config['work_type'],
                }
            )

            if not created:
                works.append(work)
                continue

            random.shuffle(available)

            for v_num in range(1, config['num_variants'] + 1):
                variant = Variant.objects.create(
                    work=work,
                    number=v_num,
                )

                start = (v_num - 1) * config['tasks_per_variant']
                end = start + config['tasks_per_variant']
                variant_tasks = available[start:end]

                if len(variant_tasks) < config['tasks_per_variant']:
                    extra = random.sample(
                        available,
                        config['tasks_per_variant'] - len(variant_tasks)
                    )
                    variant_tasks.extend(extra)

                variant.tasks.set(variant_tasks)

            works.append(work)
            self.stdout.write(
                f'  📄 {config["name"]}: {config["num_variants"]} вар. '
                f'× {config["tasks_per_variant"]} заданий'
            )

        self.stdout.write(f'📋 Работ: {len(works)}')
        return works

    def _create_course(self, works, groups):
        """Создание курса и привязка работ"""
        from curriculum.models import Course, CourseAssignment
        from datetime import date

        course, created = Course.objects.get_or_create(
            name='Физика 9 класс',
            subject='Физика',
            grade_level=9,
            academic_year='2025-2026',
            defaults={
                'description': 'Курс физики для 9 класса. Механика, силы, тепловые явления.',
                'start_date': date(2025, 9, 1),
                'end_date': date(2026, 5, 25),
                'total_hours': 68,
                'hours_per_week': 2,
                'is_active': True,
            }
        )

        # Привязываем классы
        for group in groups.values():
            course.student_groups.add(group)

        # Привязываем работы
        for i, work in enumerate(works, 1):
            CourseAssignment.objects.get_or_create(
                course=course,
                work=work,
                defaults={
                    'order': i,
                    'weight': 2.0 if 'КР' in work.name else 1.0,
                }
            )

        if created:
            self.stdout.write(f'📚 Курс: {course.name} ({len(works)} работ, {len(groups)} классов)')
        else:
            self.stdout.write(f'📚 Курс: {course.name} (уже существует)')

        return course



    def _create_events(self, works, students, groups):
        if not works:
            return

        now = timezone.now()

        events_config = [
            {
                'name': 'КР №1: Мех. движение — 9А',
                'work_name': 'КР №1: Механическое движение',
                'group_name': '9А',
                'date': now - timedelta(days=30),
            },
            {
                'name': 'КР №1: Мех. движение — 9Б',
                'work_name': 'КР №1: Механическое движение',
                'group_name': '9Б',
                'date': now - timedelta(days=28),
            },
            {
                'name': 'СР: Силы — 9А',
                'work_name': 'СР: Силы в природе',
                'group_name': '9А',
                'date': now - timedelta(days=14),
            },
            {
                'name': 'КР №2: Тепловые — 9А',
                'work_name': 'КР №2: Тепловые явления',
                'group_name': '9А',
                'date': now - timedelta(days=7),
            },
            {
                'name': 'КР №2: Тепловые — 9Б',
                'work_name': 'КР №2: Тепловые явления',
                'group_name': '9Б',
                'date': now - timedelta(days=5),
            },
        ]


        event_count = 0

        for config in events_config:
            try:
                work = Work.objects.get(name=config['work_name'])
            except Work.DoesNotExist:
                continue

            variants = list(work.variant_set.all().order_by('number'))
            if not variants:
                continue

            event, created = Event.objects.get_or_create(
                name=config['name'],
                defaults={
                    'work': work,
                    'planned_date': config['date'],
                    'status': 'graded',
                    'location': random.choice(['Каб. 301', 'Каб. 215', 'Каб. 108']),
                }
            )


            if not created:
                event_count += 1
                continue

            group_students = students[config['group_name']]

            for i, student in enumerate(group_students):
                variant = variants[i % len(variants)]
                is_absent = random.random() < 0.1

                participation = EventParticipation.objects.create(
                    event=event,
                    student=student,
                    variant=variant,
                    status='absent' if is_absent else 'assigned',
                )

                if is_absent:
                    continue

                variant_task_list = list(variant.tasks.all())
                max_points = len(variant_task_list) * 2

                level = random.choice(['weak', 'mid', 'mid', 'strong', 'strong'])
                pct_ranges = {
                    'weak': (0.3, 0.6),
                    'mid': (0.55, 0.85),
                    'strong': (0.75, 1.0),
                }
                low, high = pct_ranges[level]
                points = round(max_points * random.uniform(low, high))
                points = max(0, min(points, max_points))

                pct = points / max_points if max_points > 0 else 0
                if pct >= 0.85:
                    score = 5
                elif pct >= 0.65:
                    score = 4
                elif pct >= 0.45:
                    score = 3
                else:
                    score = 2

                task_scores = {}
                remaining = points
                for task in variant_task_list:
                    task_max = 2
                    task_pts = min(remaining, random.randint(0, task_max))
                    task_scores[str(task.pk)] = {
                        'points': task_pts,
                        'max_points': task_max,
                    }
                    remaining -= task_pts
                    if remaining <= 0:
                        remaining = 0

                Mark.objects.create(
                    participation=participation,
                    score=score,
                    points=points,
                    max_points=max_points,
                    task_scores=task_scores,
                    teacher_comment='' if random.random() > 0.3 else random.choice([
                        'Хорошая работа',
                        'Много ошибок в вычислениях',
                        'Не хватает единиц измерения',
                        'Путает формулы',
                        'Отличный результат!',
                    ]),
                    checked_at=config['date'] + timedelta(days=random.randint(1, 3)),
                )

            event_count += 1
            participations = event.eventparticipation_set.count()
            graded = Mark.objects.filter(participation__event=event).count()
            self.stdout.write(
                f'  📅 {config["name"]}: {participations} уч., {graded} оценок'
            )

        # Обновляем статусы участий
        updated = EventParticipation.objects.filter(
            mark__isnull=False
        ).exclude(status='absent').update(status='graded')
        
        absent = EventParticipation.objects.filter(status='absent').count()
        self.stdout.write(f'✅ Статусы участий обновлены: {updated} graded, {absent} absent')

        self.stdout.write(f'📅 Событий: {event_count}')

