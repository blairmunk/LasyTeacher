# core/management/commands/create_demo_events.py

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from curriculum.models import Course, CourseAssignment
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from works.models import Variant


# Профили учеников: (название, вес, генератор_оценки, генератор_баллов_процент)
STUDENT_PROFILES = [
    ('отличник',   0.15, lambda: random.choices([5, 4], weights=[80, 20])[0],       lambda mp: random.randint(int(mp*0.85), mp)),
    ('хорошист',   0.30, lambda: random.choices([5, 4, 3], weights=[20, 60, 20])[0], lambda mp: random.randint(int(mp*0.65), int(mp*0.90))),
    ('середняк',   0.30, lambda: random.choices([4, 3, 2], weights=[15, 55, 30])[0], lambda mp: random.randint(int(mp*0.40), int(mp*0.70))),
    ('слабый',     0.15, lambda: random.choices([3, 2], weights=[40, 60])[0],        lambda mp: random.randint(int(mp*0.15), int(mp*0.45))),
    ('прогульщик', 0.10, lambda: None,                                                lambda mp: 0),
]


class Command(BaseCommand):
    help = 'Создаёт демо-события: проводит работы курса, назначает варианты, выставляет оценки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course',
            type=str,
            default='Математика 7 класс',
            help='Название курса (по умолчанию: Математика 7 класс)',
        )
        parser.add_argument(
            '--group',
            type=str,
            default='7А',
            help='Название класса (по умолчанию: 7А)',
        )
        parser.add_argument(
            '--works-count',
            type=int,
            default=0,
            help='Количество работ для проведения (0 = все)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Удалить существующие демо-события перед созданием',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('🚀 Создание демо-событий...\n')

        # Находим курс
        course_name = options['course']
        try:
            course = Course.objects.get(name=course_name)
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'❌ Курс "{course_name}" не найден.\n'
                f'   Сначала создайте курс: python manage.py create_demo_course --generate-variants=4'
            ))
            return
        self.stdout.write(f'📚 Курс: {course.name}')

        # Находим класс
        group_name = options['group']
        try:
            group = StudentGroup.objects.get(name=group_name)
        except StudentGroup.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'❌ Класс "{group_name}" не найден.\n'
                f'   Доступные классы: {", ".join(StudentGroup.objects.values_list("name", flat=True))}'
            ))
            return

        students = list(group.get_active_students())
        if not students:
            self.stdout.write(self.style.ERROR(
                f'❌ В классе "{group_name}" нет учеников.'
            ))
            return
        self.stdout.write(f'🎓 Класс: {group.name} ({len(students)} учеников)')

        # Удаляем старые события если нужно
        if options['clean']:
            deleted_count = self._clean_events(course, students)
            if deleted_count:
                self.stdout.write(self.style.WARNING(
                    f'🗑️  Удалено {deleted_count} старых событий'
                ))

        # Назначаем профили ученикам
        student_profiles = self._assign_profiles(students)
        self.stdout.write(f'\n👤 Профили учеников:')
        profile_counts = {}
        for student, profile in student_profiles.items():
            profile_name = profile[0]
            profile_counts[profile_name] = profile_counts.get(profile_name, 0) + 1
        for name, count in profile_counts.items():
            self.stdout.write(f'   {name}: {count}')

        # Получаем работы курса
        assignments = course.courseassignment_set.select_related('work').order_by('order')
        works_count = options['works_count']
        if works_count > 0:
            assignments = assignments[:works_count]

        self.stdout.write(f'\n📝 Проведение {assignments.count()} работ...\n')

        events_created = 0
        participations_created = 0
        marks_created = 0
        absent_count = 0

        for ca in assignments:
            work = ca.work

            # Проверяем наличие вариантов
            variants = list(Variant.objects.filter(work=work))
            if not variants:
                self.stdout.write(self.style.WARNING(
                    f'  ⏭️ {work.name} — нет вариантов, пропускаю'
                ))
                continue

            # Дата события
            if ca.planned_date:
                event_date = timezone.make_aware(
                    datetime.combine(ca.planned_date, datetime.min.time().replace(hour=9))
                )
            else:
                event_date = timezone.now() - timedelta(days=random.randint(1, 90))

            # Создаём событие
            event, ev_created = Event.objects.update_or_create(
                name=f'{work.name} - {group.name}',
                work=work,
                course=course,
                defaults={
                    'planned_date': event_date,
                    'actual_start': event_date,
                    'actual_end': event_date + timedelta(minutes=work.duration),
                    'status': 'graded',
                    'description': f'Автоматически созданное событие для демо-базы',
                    'location': f'Кабинет {random.randint(201, 315)}',
                }
            )

            if ev_created:
                events_created += 1

            type_icon = {
                'diagnostic': '🔍', 'quiz': '📝', 'test': '📋',
                'exam': '🎓', 'homework': '🏠', 'practice': '🔧',
            }.get(work.work_type, '📄')

            self.stdout.write(f'  {type_icon} {work.name}')

            # Создаём участия и оценки
            event_marks = []
            for student in students:
                profile = student_profiles[student]
                profile_name, _, score_gen, points_gen = profile

                # Создаём участие
                participation, p_created = EventParticipation.objects.update_or_create(
                    event=event,
                    student=student,
                    defaults={
                        'variant': random.choice(variants),
                    }
                )
                if p_created:
                    participations_created += 1

                # Прогульщик
                if profile_name == 'прогульщик' and random.random() < 0.4:
                    participation.status = 'absent'
                    participation.save()
                    absent_count += 1
                    continue

                # Генерируем оценку
                score = score_gen()
                if score is None:
                    participation.status = 'absent'
                    participation.save()
                    absent_count += 1
                    continue

                participation.status = 'graded'
                participation.started_at = event_date
                participation.completed_at = event_date + timedelta(
                    minutes=random.randint(int(work.duration * 0.5), work.duration)
                )
                participation.graded_at = event_date + timedelta(days=random.randint(1, 3))
                participation.save()

                # Баллы
                max_points = work.duration  # упрощение: макс баллов = длительность
                points = points_gen(max_points)

                # Детализация по заданиям
                task_scores = {}
                if participation.variant:
                    variant_tasks = list(participation.variant.tasks.all())
                    points_per_task = max_points // max(len(variant_tasks), 1)
                    for task in variant_tasks:
                        task_max = points_per_task
                        # Распределяем баллы в зависимости от оценки
                        if score >= 4:
                            task_pts = random.randint(
                                int(task_max * 0.6), task_max
                            )
                        elif score == 3:
                            task_pts = random.randint(
                                int(task_max * 0.2), int(task_max * 0.7)
                            )
                        else:
                            task_pts = random.randint(0, int(task_max * 0.4))

                        task_scores[str(task.id)] = {
                            'points': task_pts,
                            'max_points': task_max,
                            'comment': '',
                        }

                # Создаём оценку
                mark, m_created = Mark.objects.update_or_create(
                    participation=participation,
                    defaults={
                        'score': score,
                        'points': points,
                        'max_points': max_points,
                        'task_scores': task_scores,
                        'checked_at': participation.graded_at,
                        'checked_by': 'Демо-учитель',
                        'is_excellent': score == 5 and random.random() < 0.3,
                        'needs_attention': score == 2,
                        'teacher_comment': self._generate_comment(score),
                    }
                )
                if m_created:
                    marks_created += 1
                event_marks.append(score)

            # Статистика по событию
            if event_marks:
                avg = sum(event_marks) / len(event_marks)
                fives = event_marks.count(5)
                twos = event_marks.count(2)
                self.stdout.write(
                    f'     {len(event_marks)} уч. | '
                    f'ср: {avg:.1f} | '
                    f'5:{fives} 4:{event_marks.count(4)} '
                    f'3:{event_marks.count(3)} 2:{twos}'
                )

        # Итоги
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS('📊 ИТОГИ:'))
        self.stdout.write(f'  📅 Событий создано: {events_created}')
        self.stdout.write(f'  👤 Участий создано: {participations_created}')
        self.stdout.write(f'  📝 Оценок выставлено: {marks_created}')
        self.stdout.write(f'  🚫 Отсутствовали: {absent_count}')

        # Общая статистика по оценкам
        all_marks = Mark.objects.filter(
            participation__event__course=course,
            participation__student__in=students,
            score__isnull=False,
        )
        if all_marks.exists():
            from django.db.models import Avg, Count
            stats = all_marks.aggregate(
                avg_score=Avg('score'),
                total=Count('id'),
            )
            self.stdout.write(f'\n  📈 Средний балл по курсу: {stats["avg_score"]:.2f}')
            self.stdout.write(f'  📊 Всего оценок: {stats["total"]}')

            # Распределение
            for score_val in [5, 4, 3, 2]:
                count = all_marks.filter(score=score_val).count()
                pct = count / stats['total'] * 100
                bar = '█' * int(pct / 2)
                self.stdout.write(f'     {score_val}: {count:3d} ({pct:4.1f}%) {bar}')

        self.stdout.write(f'\n  🌐 События: http://127.0.0.1:8000/events/')
        self.stdout.write(f'  🌐 Курс: http://127.0.0.1:8000/curriculum/courses/{course.pk}/')

    def _assign_profiles(self, students):
        """Назначить каждому ученику профиль успеваемости"""
        profiles = {}
        weights = [p[1] for p in STUDENT_PROFILES]

        for student in students:
            # Детерминированный выбор на основе UUID (стабильный при повторных запусках)
            random.seed(str(student.id))
            profile = random.choices(STUDENT_PROFILES, weights=weights, k=1)[0]
            profiles[student] = profile

        # Сбросить seed
        random.seed()
        return profiles

    def _generate_comment(self, score):
        """Генерация комментария учителя"""
        comments = {
            5: [
                'Отличная работа!',
                'Молодец, все задания выполнены верно.',
                'Прекрасный результат, так держать!',
                'Безупречное выполнение.',
            ],
            4: [
                'Хорошая работа, но есть небольшие недочёты.',
                'В целом хорошо, обратите внимание на оформление.',
                'Хороший результат. Проверьте вычисления.',
                'Почти отлично, будьте внимательнее.',
            ],
            3: [
                'Необходимо повторить материал.',
                'Есть существенные пробелы в знаниях.',
                'Нужно больше тренироваться.',
                'Обратитесь за дополнительной помощью.',
            ],
            2: [
                'Работа не выполнена на удовлетворительном уровне.',
                'Необходима пересдача и дополнительные занятия.',
                'Материал не усвоен. Рекомендуется индивидуальная работа.',
                'Требуется серьёзная работа над ошибками.',
            ],
        }
        options = comments.get(score, [''])
        return random.choice(options)

    def _clean_events(self, course, students):
        """Удалить демо-события"""
        events = Event.objects.filter(
            course=course,
            description__contains='демо-базы',
        )
        count = events.count()
        events.delete()
        return count
