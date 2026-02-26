# core/management/commands/populate_demo_students.py

import random
from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import Student, StudentGroup


LAST_NAMES = [
    'Абрамов', 'Алексеев', 'Андреев', 'Баранов', 'Белов',
    'Богданов', 'Борисов', 'Васильев', 'Виноградов', 'Власов',
    'Воробьёв', 'Герасимов', 'Горбунов', 'Григорьев', 'Давыдов',
    'Дмитриев', 'Егоров', 'Жуков', 'Зайцев', 'Захаров',
    'Ильин', 'Калинин', 'Киселёв', 'Козлов', 'Колесников',
    'Комаров', 'Коновалов', 'Королёв', 'Крылов', 'Кудрявцев',
    'Кузьмин', 'Лазарев', 'Лебедев', 'Макаров', 'Максимов',
    'Марков', 'Медведев', 'Михайлов', 'Морозов', 'Назаров',
    'Никитин', 'Николаев', 'Новиков', 'Орлов', 'Осипов',
    'Павлов', 'Пономарёв', 'Попов', 'Романов', 'Савельев',
    'Семёнов', 'Сергеев', 'Сидоров', 'Соколов', 'Степанов',
    'Суханов', 'Тарасов', 'Тимофеев', 'Титов', 'Фёдоров',
    'Филиппов', 'Фомин', 'Цветков', 'Чернов', 'Шевченко',
    'Щербаков', 'Яковлев',
]

MALE_FIRST_NAMES = [
    'Александр', 'Алексей', 'Андрей', 'Антон', 'Артём',
    'Богдан', 'Вадим', 'Виктор', 'Владимир', 'Глеб',
    'Даниил', 'Дмитрий', 'Евгений', 'Егор', 'Иван',
    'Игорь', 'Кирилл', 'Константин', 'Лев', 'Максим',
    'Матвей', 'Михаил', 'Никита', 'Николай', 'Олег',
    'Павел', 'Роман', 'Сергей', 'Степан', 'Тимофей',
    'Фёдор', 'Ярослав',
]

FEMALE_FIRST_NAMES = [
    'Алина', 'Анастасия', 'Анна', 'Валерия', 'Варвара',
    'Вероника', 'Виктория', 'Дарья', 'Евгения', 'Екатерина',
    'Елена', 'Елизавета', 'Ирина', 'Ксения', 'Мария',
    'Милана', 'Наталья', 'Ольга', 'Полина', 'Светлана',
    'София', 'Татьяна', 'Ульяна', 'Юлия',
]

MALE_PATRONYMICS = [
    'Александрович', 'Алексеевич', 'Андреевич', 'Артёмович',
    'Владимирович', 'Дмитриевич', 'Евгеньевич', 'Иванович',
    'Игоревич', 'Максимович', 'Михайлович', 'Николаевич',
    'Олегович', 'Павлович', 'Романович', 'Сергеевич',
]

FEMALE_PATRONYMICS = [
    'Александровна', 'Алексеевна', 'Андреевна', 'Артёмовна',
    'Владимировна', 'Дмитриевна', 'Евгеньевна', 'Ивановна',
    'Игоревна', 'Максимовна', 'Михайловна', 'Николаевна',
    'Олеговна', 'Павловна', 'Романовна', 'Сергеевна',
]


class Command(BaseCommand):
    help = 'Добавляет реалистичных учеников в классы для демо'

    def add_arguments(self, parser):
        parser.add_argument(
            '--groups',
            nargs='+',
            default=['7А', '7Б'],
            help='Классы для наполнения (по умолчанию: 7А 7Б)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=25,
            help='Количество учеников в каждом классе (по умолчанию: 25)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Удалить существующих учеников перед созданием',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('🚀 Наполнение классов учениками...\n')

        # Диагностика: поля модели Student
        self.stdout.write('📋 Поля модели Student:')
        for f in Student._meta.get_fields():
            self.stdout.write(f'   {f.name} ({type(f).__name__})')
        self.stdout.write('')

        # Диагностика: поля модели StudentGroup
        self.stdout.write('📋 Поля модели StudentGroup:')
        for f in StudentGroup._meta.get_fields():
            self.stdout.write(f'   {f.name} ({type(f).__name__})')
        self.stdout.write('')

        target_count = options['count']
        total_created = 0
        total_existing = 0

        for group_name in options['groups']:
            try:
                group = StudentGroup.objects.get(name=group_name)
            except StudentGroup.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'⚠️ Класс "{group_name}" не найден, пропускаю'
                ))
                continue

            # Получаем текущих учеников группы
            current_students = self._get_group_students(group)
            existing_count = len(current_students)
            self.stdout.write(f'\n🎓 {group.name}: сейчас {existing_count} учеников')

            if options['clean']:
                deleted = self._clean_group_students(group)
                if deleted:
                    self.stdout.write(self.style.WARNING(
                        f'   🗑️ Удалено {deleted} учеников'
                    ))
                existing_count = 0
                current_students = []

            needed = target_count - existing_count
            if needed <= 0:
                self.stdout.write(f'   ✅ Уже {existing_count} учеников, достаточно')
                total_existing += existing_count
                continue

            # Существующие имена в классе
            existing_names = set(
                (s.last_name, s.first_name) for s in current_students
            )

            # Генерируем учеников
            created = 0
            random.seed(f'students_{group_name}_2024')

            available_last_names = LAST_NAMES.copy()
            random.shuffle(available_last_names)

            attempts = 0
            max_attempts = needed * 5

            while created < needed and attempts < max_attempts:
                attempts += 1

                is_male = random.random() < 0.5

                last_name = random.choice(available_last_names)
                if is_male:
                    first_name = random.choice(MALE_FIRST_NAMES)
                    middle_name = random.choice(MALE_PATRONYMICS)
                else:
                    last_name = self._feminize_last_name(last_name)
                    first_name = random.choice(FEMALE_FIRST_NAMES)
                    middle_name = random.choice(FEMALE_PATRONYMICS)

                name_key = (last_name, first_name)
                if name_key in existing_names:
                    continue
                existing_names.add(name_key)

                # Создаём ученика с реальными полями модели
                create_kwargs = {
                    'last_name': last_name,
                    'first_name': first_name,
                    'middle_name': middle_name,
                }

                # email — если поле есть
                email = (
                    f'{self._transliterate(last_name).lower()}'
                    f'.{self._transliterate(first_name).lower()}'
                    f'@school.demo'
                )
                create_kwargs['email'] = email

                student = Student.objects.create(**create_kwargs)

                # Привязываем к группе
                self._add_student_to_group(group, student)

                created += 1

            random.seed()

            total_created += created
            total_existing += existing_count

            final_students = self._get_group_students(group)
            self.stdout.write(self.style.SUCCESS(
                f'   ✅ Добавлено {created} учеников → итого {len(final_students)}'
            ))

            for s in sorted(final_students, key=lambda s: (s.last_name, s.first_name)):
                self.stdout.write(
                    f'      {s.last_name} {s.first_name} {s.middle_name}'
                )

        # Итоги
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS('📊 ИТОГИ:'))
        self.stdout.write(f'  👤 Создано учеников: {total_created}')
        self.stdout.write(f'  👥 Уже было: {total_existing}')
        self.stdout.write(f'  📊 Всего в базе: {Student.objects.count()} учеников')

    def _get_group_students(self, group):
        """Получить учеников группы — универсально"""
        # Пробуем разные варианты связи
        if hasattr(group, 'students'):
            return list(group.students.all())
        if hasattr(group, 'student_set'):
            return list(group.student_set.all())
        if hasattr(group, 'get_active_students'):
            return list(group.get_active_students())
        # Через обратную связь
        return list(Student.objects.filter(studentgroup=group))

    def _add_student_to_group(self, group, student):
        """Добавить ученика в группу — универсально"""
        if hasattr(group, 'students'):
            # M2M
            group.students.add(student)
        elif hasattr(group, 'student_set'):
            group.student_set.add(student)
        else:
            # Попробуем через промежуточную модель
            # Если StudentGroup имеет M2M через through
            try:
                group.students.add(student)
            except Exception:
                pass

    def _clean_group_students(self, group):
        """Удалить учеников из группы"""
        students = self._get_group_students(group)
        count = len(students)
        for s in students:
            s.delete()
        return count

    def _feminize_last_name(self, last_name):
        """Феминизация фамилии"""
        if last_name.endswith('ов'):
            return last_name + 'а'
        elif last_name.endswith('ев') or last_name.endswith('ёв'):
            return last_name + 'а'
        elif last_name.endswith('ин'):
            return last_name + 'а'
        elif last_name.endswith('ко'):
            return last_name
        else:
            return last_name + 'а'

    def _transliterate(self, text):
        """Транслитерация для email"""
        mapping = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
            'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
            'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
            'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        result = ''
        for char in text.lower():
            result += mapping.get(char, char)
        return result
