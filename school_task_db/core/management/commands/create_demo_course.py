# core/management/commands/create_demo_course.py

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta

from curriculum.models import Course, CourseAssignment
from works.models import Work, WorkAnalogGroup
from task_groups.models import AnalogGroup


# Структура демо-курса
DEMO_COURSE = {
    'name': 'Математика 7 класс',
    'subject': 'Математика',
    'grade_level': 7,
    'academic_year': '2024-2025',
    'hours_per_week': 5,
    'total_hours': 170,
    'description': 'Основной курс математики для 7 класса. '
                   'Включает алгебру, геометрию, вероятность и статистику.',
    'works': [
        {
            'name': 'Входная диагностика: Повторение 6 класса',
            'work_type': 'diagnostic',
            'duration': 40,
            'week_offset': 1,
            'groups': [
                ('Сложение и вычитание дробей', 2),
                ('Умножение и деление дробей', 1),
                ('Действия с десятичными дробями', 2),
            ]
        },
        {
            'name': 'Самостоятельная работа: Линейные уравнения (базовый)',
            'work_type': 'quiz',
            'duration': 25,
            'week_offset': 3,
            'groups': [
                ('Линейные уравнения — базовый', 3),
            ]
        },
        {
            'name': 'Самостоятельная работа: Линейные уравнения (повышенный)',
            'work_type': 'quiz',
            'duration': 30,
            'week_offset': 4,
            'groups': [
                ('Линейные уравнения — базовый', 1),
                ('Линейные уравнения — повышенный', 2),
            ]
        },
        {
            'name': 'Контрольная работа №1: Линейные уравнения',
            'work_type': 'test',
            'duration': 45,
            'week_offset': 5,
            'groups': [
                ('Линейные уравнения — базовый', 2),
                ('Линейные уравнения — повышенный', 2),
            ]
        },
        {
            'name': 'Самостоятельная работа: Степени',
            'work_type': 'quiz',
            'duration': 25,
            'week_offset': 7,
            'groups': [
                ('Степень с натуральным показателем', 3),
            ]
        },
        {
            'name': 'Самостоятельная работа: Многочлены',
            'work_type': 'quiz',
            'duration': 30,
            'week_offset': 9,
            'groups': [
                ('Раскрытие скобок и упрощение', 3),
            ]
        },
        {
            'name': 'Контрольная работа №2: Степени и многочлены',
            'work_type': 'test',
            'duration': 45,
            'week_offset': 10,
            'groups': [
                ('Степень с натуральным показателем', 2),
                ('Раскрытие скобок и упрощение', 2),
            ]
        },
        {
            'name': 'Самостоятельная работа: Геометрия — углы',
            'work_type': 'quiz',
            'duration': 25,
            'week_offset': 12,
            'groups': [
                ('Углы треугольника', 3),
            ]
        },
        {
            'name': 'Самостоятельная работа: Геометрия — площадь',
            'work_type': 'quiz',
            'duration': 30,
            'week_offset': 14,
            'groups': [
                ('Площадь треугольника', 3),
            ]
        },
        {
            'name': 'Контрольная работа №3: Треугольники',
            'work_type': 'test',
            'duration': 45,
            'week_offset': 15,
            'groups': [
                ('Углы треугольника', 2),
                ('Площадь треугольника', 2),
            ]
        },
        {
            'name': 'Самостоятельная работа: Текстовые задачи',
            'work_type': 'quiz',
            'duration': 30,
            'week_offset': 17,
            'groups': [
                ('Задачи на движение', 2),
                ('Задачи на проценты', 2),
            ]
        },
        {
            'name': 'Самостоятельная работа: Вероятность',
            'work_type': 'quiz',
            'duration': 25,
            'week_offset': 19,
            'groups': [
                ('Вероятность событий', 3),
            ]
        },
        {
            'name': 'Итоговая контрольная работа за I полугодие',
            'work_type': 'exam',
            'duration': 60,
            'week_offset': 20,
            'groups': [
                ('Линейные уравнения — базовый', 1),
                ('Линейные уравнения — повышенный', 1),
                ('Степень с натуральным показателем', 1),
                ('Раскрытие скобок и упрощение', 1),
                ('Углы треугольника', 1),
                ('Площадь треугольника', 1),
                ('Задачи на движение', 1),
                ('Вероятность событий', 1),
            ]
        },
    ]
}


class Command(BaseCommand):
    help = 'Создаёт демо-курс с работами из импортированных групп аналогов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Удалить существующий демо-курс перед созданием',
        )
        parser.add_argument(
            '--generate-variants',
            type=int,
            default=0,
            metavar='N',
            help='Сгенерировать N вариантов для каждой работы',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('🚀 Создание демо-курса...\n')

        # Проверяем наличие групп аналогов
        available_groups = {g.name: g for g in AnalogGroup.objects.all()}
        self.stdout.write(f'📦 Доступно групп аналогов: {len(available_groups)}')

        if len(available_groups) == 0:
            self.stdout.write(self.style.ERROR(
                '❌ Нет групп аналогов! Сначала импортируйте задания:\n'
                '   python manage.py import_tasks data/demo_tasks.json '
                '--mode=update --verbose --create-topics'
            ))
            return

        # Удаляем старый демо-курс если нужно
        if options['clean']:
            deleted = self._clean_demo_course()
            if deleted:
                self.stdout.write(self.style.WARNING(
                    f'🗑️  Удалён предыдущий демо-курс'
                ))

        # Создаём курс
        course_data = DEMO_COURSE
        start_date = date(2024, 9, 2)  # 2 сентября

        course, created = Course.objects.update_or_create(
            name=course_data['name'],
            subject=course_data['subject'],
            grade_level=course_data['grade_level'],
            academic_year=course_data['academic_year'],
            defaults={
                'description': course_data['description'],
                'hours_per_week': course_data['hours_per_week'],
                'total_hours': course_data['total_hours'],
                'start_date': start_date,
                'end_date': date(2025, 5, 30),
                'is_active': True,
            }
        )
        action = 'Создан' if created else 'Обновлён'
        self.stdout.write(self.style.SUCCESS(
            f'\n📚 {action} курс: {course.name}'
        ))

        # Привязываем классы к курсу
        from students.models import StudentGroup
        grade = course_data['grade_level']
        matching_groups = StudentGroup.objects.filter(
            name__startswith=str(grade)
        )
        if matching_groups.exists():
            course.student_groups.set(matching_groups)
            group_names = ', '.join(g.name for g in matching_groups)
            self.stdout.write(f'  🎓 Привязаны классы: {group_names}')

        # Создаём работы
        works_created = 0
        works_skipped = 0
        groups_linked = 0
        missing_groups = set()

        for i, work_data in enumerate(course_data['works'], 1):
            # Проверяем наличие всех групп
            work_groups = []
            skip_work = False

            for group_name, count in work_data['groups']:
                if group_name in available_groups:
                    work_groups.append((available_groups[group_name], count))
                else:
                    missing_groups.add(group_name)
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️ Группа "{group_name}" не найдена — '
                        f'работа "{work_data["name"]}" будет неполной'
                    ))

            if not work_groups:
                self.stdout.write(self.style.WARNING(
                    f'  ⏭️ Пропущена работа "{work_data["name"]}" — '
                    f'нет доступных групп'
                ))
                works_skipped += 1
                continue

            # Создаём работу
            planned_date = start_date + timedelta(weeks=work_data['week_offset'])

            work, w_created = Work.objects.update_or_create(
                name=work_data['name'],
                defaults={
                    'work_type': work_data['work_type'],
                    'duration': work_data['duration'],
                }
            )

            # Связываем с группами аналогов
            WorkAnalogGroup.objects.filter(work=work).delete()
            for analog_group, count in work_groups:
                WorkAnalogGroup.objects.create(
                    work=work,
                    analog_group=analog_group,
                    count=count,
                )
                groups_linked += 1

            # Привязываем к курсу
            CourseAssignment.objects.update_or_create(
                course=course,
                work=work,
                defaults={
                    'order': i,
                    'planned_date': planned_date,
                    'weight': 2.0 if work_data['work_type'] in ('test', 'exam') else 1.0,
                }
            )

            type_icon = {
                'diagnostic': '🔍',
                'quiz': '📝',
                'test': '📋',
                'exam': '🎓',
                'homework': '🏠',
                'practice': '🔧',
            }.get(work_data['work_type'], '📄')

            total_tasks = sum(c for _, c in work_groups)
            if w_created:
                works_created += 1
            self.stdout.write(
                f'  {type_icon} #{i:2d} {work_data["name"]}\n'
                f'       {len(work_groups)} групп, {total_tasks} заданий/вариант, '
                f'{work_data["duration"]} мин | {planned_date:%d.%m.%Y}'
            )

        # Генерация вариантов
        variants_total = 0
        gen_count = options['generate_variants']
        if gen_count > 0:
            self.stdout.write(f'\n🎲 Генерация {gen_count} вариантов для каждой работы...')
            for ca in course.courseassignment_set.select_related('work'):
                work = ca.work
                variants = work.generate_variants(count=gen_count)
                variants_total += len(variants)
                for v in variants:
                    tasks_count = v.tasks.count()
                    self.stdout.write(
                        f'  ✅ {work.name} → Вариант {v.number} '
                        f'({tasks_count} заданий)'
                    )

        # Итоги
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS('📊 ИТОГИ:'))
        self.stdout.write(f'  📚 Курс: {course.name}')
        self.stdout.write(f'  📝 Работ создано: {works_created}')
        if works_skipped:
            self.stdout.write(f'  ⏭️ Работ пропущено: {works_skipped}')
        self.stdout.write(f'  🔗 Связей с группами: {groups_linked}')
        if variants_total:
            self.stdout.write(f'  🎲 Вариантов создано: {variants_total}')
        if missing_groups:
            self.stdout.write(self.style.WARNING(
                f'  ⚠️ Не найдено групп: {", ".join(missing_groups)}'
            ))
        self.stdout.write(f'\n  🌐 Курс: http://127.0.0.1:8000/curriculum/courses/{course.pk}/')
        self.stdout.write(f'  🌐 Работы: http://127.0.0.1:8000/works/')

    def _clean_demo_course(self):
        """Удаление демо-курса и связанных работ"""
        try:
            course = Course.objects.get(
                name=DEMO_COURSE['name'],
                academic_year=DEMO_COURSE['academic_year'],
            )
            # Удаляем работы, которые принадлежат только этому курсу
            for ca in course.courseassignment_set.all():
                work = ca.work
                # Проверяем, не привязана ли работа к другим курсам
                if work.courseassignment_set.count() == 1:
                    work.delete()
            course.delete()
            return True
        except Course.DoesNotExist:
            return False
