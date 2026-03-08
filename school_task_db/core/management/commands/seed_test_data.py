"""
Создание тестовых данных для school_task_db.
python manage.py seed_test_data [--clear]
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone as tz

from curriculum.models import Topic, SubTopic, Course
from tasks.models import Task
from task_groups.models import AnalogGroup, TaskGroup
from students.models import Student, StudentGroup, StudentTaskLog
from works.models import Work, Variant, VariantTask
from events.models import Event, EventParticipation, Mark


# ═══════════════════════════════════════════════
#  ДАННЫЕ
# ═══════════════════════════════════════════════

SUBJECT = 'Физика'
GRADE = 9

TOPICS_DATA = [
    ('Механическое движение', 'Механика',
     'Равномерное и неравномерное движение, скорость, путь'),
    ('Плотность вещества', 'Механика',
     'Плотность, масса, объём'),
    ('Силы в природе', 'Механика',
     'Сила тяжести, упругости, трения'),
    ('Количество теплоты', 'Термодинамика',
     'Теплопередача, удельная теплоёмкость'),
    ('Агрегатные состояния', 'Термодинамика',
     'Плавление, парообразование, конденсация'),
]

# (group_name, topic_index, group_difficulty,
#  [(text, answer, difficulty, task_type), ...])
GROUPS_DATA = [
    ('Равномерное движение: скорость', 0, 2, [
        ('Автомобиль проехал 60 км за 1 час. Чему равна его скорость?',
         '60 км/ч', 1, 'short_answer'),
        ('Поезд движется со скоростью 72 км/ч. Какое расстояние он проедет за 2,5 часа?',
         '180 км', 2, 'short_answer'),
        ('Велосипедист проехал 30 км за 1,5 часа. Найдите его скорость в м/с.',
         r'$v = \frac{30000}{5400} \approx 5{,}6$ м/с', 2, 'open'),
        ('Из пунктов A и B, расстояние между которыми 120 км, одновременно навстречу друг другу выехали два автомобиля со скоростями 60 км/ч и 80 км/ч. Через сколько часов они встретятся?',
         r'$t = \frac{120}{60+80} \approx 0{,}86$ ч $\approx 51{,}4$ мин', 4, 'open'),
        ('Мотоциклист ехал первую треть пути со скоростью $v_1 = 60$ км/ч, а оставшуюся часть — со скоростью $v_2 = 80$ км/ч. Найдите среднюю скорость.',
         r'$v_{ср} = \frac{3v_1 v_2}{v_1 + 2v_2} = \frac{3 \cdot 60 \cdot 80}{60 + 160} \approx 72{,}7$ км/ч', 5, 'open'),
        ('Два поезда выехали одновременно навстречу друг другу. Первый проехал до встречи на 100 км больше второго. Скорость первого 80 км/ч, второго — 60 км/ч. Найдите расстояние между городами.',
         r'$S = \frac{100(v_1+v_2)}{v_1-v_2} = 700$ км', 6, 'open'),
    ]),
    ('Средняя скорость', 0, 2, [
        ('Пешеход прошёл 3 км за 40 минут. Найдите среднюю скорость в км/ч.',
         '4,5 км/ч', 1, 'short_answer'),
        ('Автомобиль проехал первые 100 км за 1 час, а следующие 150 км за 2 часа. Найдите среднюю скорость.',
         r'$v_{ср} = \frac{250}{3} \approx 83{,}3$ км/ч', 2, 'short_answer'),
        ('Турист шёл 2 часа со скоростью 5 км/ч, затем 3 часа — со скоростью 4 км/ч. Найдите среднюю скорость.',
         r'$v_{ср} = \frac{10+12}{5} = 4{,}4$ км/ч', 2, 'open'),
        ('Первую половину пути автомобиль ехал со скоростью 40 км/ч, а вторую — со скоростью 60 км/ч. Найдите среднюю скорость на всём пути.',
         r'$v_{ср} = \frac{2v_1 v_2}{v_1+v_2} = 48$ км/ч', 4, 'open'),
        ('Тело двигалось первую треть времени со скоростью 2 м/с, вторую треть — 4 м/с, последнюю — 6 м/с. Определите среднюю скорость и средний модуль скорости.',
         '4 м/с', 5, 'open'),
    ]),
    ('Плотность: расчёты', 1, 2, [
        ('Масса тела 500 г, объём 100 см³. Чему равна плотность?',
         r'$\rho = 5$ г/см³ = 5000 кг/м³', 1, 'short_answer'),
        ('Плотность алюминия 2700 кг/м³. Найдите массу куба с ребром 10 см.',
         '2,7 кг', 2, 'short_answer'),
        ('Стальной шарик имеет массу 39,25 г. Определите его радиус, если $\\rho = 7850$ кг/м³.',
         r'$r = \sqrt[3]{\frac{3m}{4\pi\rho}} \approx 0{,}01$ м = 1 см', 4, 'open'),
        ('Полый шар из свинца имеет внешний радиус 5 см и массу 2 кг. Найдите объём полости.',
         r'$V_{пол} = V_{внеш} - \frac{m}{\rho} \approx 347$ см³', 5, 'open'),
        ('Сплав состоит из золота и серебра. Масса сплава 500 г, объём 30 см³. Найдите массу золота.',
         r'Система уравнений: $m_{Au} \approx 346$ г', 6, 'open'),
    ]),
    ('Сила тяжести и вес', 2, 2, [
        ('Масса мешка 50 кг. Чему равна сила тяжести? ($g = 10$ м/с²)',
         '500 Н', 1, 'short_answer'),
        ('Сила тяжести, действующая на камень, равна 15 Н. Найдите его массу.',
         '1,5 кг', 2, 'short_answer'),
        ('Определите вес человека массой 70 кг в лифте, движущемся вверх с ускорением 2 м/с².',
         r'$P = m(g+a) = 70 \cdot 12 = 840$ Н', 2, 'open'),
        ('Тело массой 5 кг висит на двух нитях, составляющих углы 30° и 60° с горизонтом. Найдите натяжение каждой нити.',
         r'$T_1 = mg\cos 60° / \sin 90° = 25$ Н, $T_2 = mg\cos 30° / \sin 90° \approx 43{,}3$ Н', 4, 'open'),
        ('Тело скользит по наклонной плоскости с углом 30° с постоянной скоростью. Найдите коэффициент трения.',
         r'$\mu = \tan 30° \approx 0{,}577$', 5, 'open'),
    ]),
    ('Закон Гука', 2, 2, [
        ('Пружину жёсткостью 100 Н/м растянули на 5 см. Чему равна сила упругости?',
         '5 Н', 1, 'short_answer'),
        ('Под действием силы 20 Н пружина удлинилась на 4 см. Найдите жёсткость пружины.',
         '500 Н/м', 2, 'short_answer'),
        ('Две пружины жёсткостью $k_1 = 100$ Н/м и $k_2 = 200$ Н/м соединены последовательно. Найдите удлинение системы под действием силы 12 Н.',
         r'$\Delta l = F/k_1 + F/k_2 = 0{,}18$ м', 4, 'open'),
        ('Две пружины соединены параллельно. $k_1 = 300$ Н/м, $k_2 = 200$ Н/м. Груз массой 5 кг подвешен к системе. Найдите удлинение.',
         r'$\Delta l = \frac{mg}{k_1+k_2} = 0{,}1$ м', 4, 'open'),
        ('К системе из трёх пружин (две параллельно, последовательно с третьей) приложена сила. Найдите удлинение каждой пружины.',
         'Задача на комбинированное соединение', 6, 'open'),
    ]),
    ('Количество теплоты: нагревание', 3, 2, [
        ('Сколько теплоты нужно для нагревания 2 кг воды на 10°C? ($c = 4200$ Дж/(кг·°C))',
         '84000 Дж = 84 кДж', 1, 'short_answer'),
        ('Для нагревания 500 г вещества от 20°C до 70°C потребовалось 25 кДж. Определите удельную теплоёмкость.',
         '1000 Дж/(кг·°C)', 2, 'short_answer'),
        ('Алюминиевую деталь массой 2 кг нагрели от 20°C до 200°C. Сколько теплоты она получила? ($c_{Al} = 920$ Дж/(кг·°C))',
         '331200 Дж ≈ 331 кДж', 2, 'open'),
        ('В калориметр с водой массой 200 г при 20°C опустили медный брусок массой 300 г при 100°C. Найдите конечную температуру. ($c_{Cu} = 400$ Дж/(кг·°C))',
         r'$t = \frac{c_в m_в t_в + c_{Cu} m_{Cu} t_{Cu}}{c_в m_в + c_{Cu} m_{Cu}} \approx 31{,}8°C$', 4, 'open'),
        ('Смесь из воды и льда находится при 0°C. В неё вливают 500 г воды при 80°C. Вся смесь нагрелась до 10°C. Найдите начальную массу льда.',
         r'$m_{льда} = \frac{c_в \cdot 0{,}5 \cdot 70 - c_в m_в \cdot 10}{L + c_в \cdot 10}$', 5, 'open'),
    ]),
    ('Уравнение теплового баланса', 3, 4, [
        ('В 200 г воды при 80°C опустили 100 г воды при 20°C. Найдите конечную температуру.',
         '60°C', 2, 'short_answer'),
        ('В калориметр налили 300 г воды при 25°C и опустили нагретый до 100°C стальной шарик массой 50 г. Конечная температура 27°C. Найдите удельную теплоёмкость стали.',
         r'$c = \frac{c_в m_в \Delta t_в}{m \Delta t} \approx 500$ Дж/(кг·°C)', 4, 'short_answer'),
        ('В медный калориметр массой 100 г, содержащий 500 г воды при 15°C, опустили кусок льда при 0°C. Конечная температура 5°C. Найдите массу льда.',
         r'$m_{льда} \approx 60$ г', 4, 'open'),
        ('Свинцовая пуля, летящая со скоростью 400 м/с, попадает в стену и останавливается. На сколько градусов нагреется пуля, если 60% кинетической энергии идёт на её нагрев?',
         r'$\Delta t = \frac{0{,}6 \cdot v^2}{2c} \approx 369°C$', 5, 'open'),
        ('Три жидкости смешивают в калориметре. Первая: $m_1, c_1, t_1$. Вторая: $m_2, c_2, t_2$. Третья: $m_3, c_3, t_3$. Выведите формулу конечной температуры и решите при заданных значениях.',
         'Вывод формулы + числовой ответ', 6, 'open'),
    ]),
    ('Плавление и кристаллизация', 4, 2, [
        ('Сколько теплоты нужно для плавления 2 кг льда при 0°C? ($L = 330$ кДж/кг)',
         '660 кДж', 1, 'short_answer'),
        ('Для плавления 500 г вещества потребовалось 59 кДж. Определите удельную теплоту плавления.',
         '118 кДж/кг', 2, 'short_answer'),
        ('Сколько теплоты нужно, чтобы 3 кг льда при $-10°C$ превратить в воду при $0°C$?',
         r'$Q = cm\Delta t + Lm = 63 + 990 = 1053$ кДж', 2, 'open'),
        ('Кусок льда массой 200 г при $-20°C$ бросили в 500 г воды при 50°C. Что получится? Найдите конечную температуру.',
         r'$t \approx 21°C$', 4, 'open'),
        ('На нагреватель мощностью 1 кВт положили кусок льда при $-30°C$. Через какое время вся вода нагреется до 100°C? Масса льда 2 кг.',
         r'$t \approx 17{,}5$ мин', 5, 'open'),
    ]),
    ('Парообразование и конденсация', 4, 2, [
        ('Сколько теплоты выделится при конденсации 100 г водяного пара при 100°C? ($L = 2260$ кДж/кг)',
         '226 кДж', 1, 'short_answer'),
        ('Для испарения 200 г жидкости потребовалось 460 кДж. Определите удельную теплоту парообразования.',
         '2300 кДж/кг', 2, 'short_answer'),
        ('Сколько теплоты нужно, чтобы 500 г воды при 20°C превратить в пар при 100°C?',
         r'$Q = cm\Delta t + Lm = 168 + 1130 = 1298$ кДж', 2, 'open'),
        ('В герметичный сосуд с 1 кг воды при 20°C впустили 100 г пара при 100°C. Найдите конечную температуру.',
         r'$t \approx 68°C$', 4, 'open'),
        ('Какую минимальную мощность должен иметь кипятильник, чтобы за 10 минут вскипятить 1 л воды при 20°C в сосуде, теряющем 30% теплоты?',
         r'$P \approx 800$ Вт', 5, 'open'),
    ]),
    ('КПД нагревателя', 3, 4, [
        ('Электрочайник мощностью 2 кВт вскипятил 1 л воды от 20°C за 3 минуты. Найдите КПД.',
         r'$\eta = \frac{Q_{полезн}}{Q_{затр}} = \frac{336000}{360000} \approx 93\%$', 2, 'short_answer'),
        ('При сжигании 100 г керосина ($q = 46$ МДж/кг) нагрели 5 кг воды от 15°C до 75°C. Найдите КПД.',
         r'$\eta = \frac{cm\Delta t}{qm_{топл}} = \frac{1260000}{4600000} \approx 27{,}4\%$', 4, 'open'),
        ('Двигатель внутреннего сгорания имеет КПД 35%. Расход топлива 10 л/100 км. Плотность бензина 750 кг/м³, $q = 46$ МДж/кг. Какова мощность двигателя на скорости 72 км/ч?',
         r'$P \approx 24{,}2$ кВт', 5, 'open'),
        ('Тепловая машина работает по циклу Карно между температурами 400 К и 300 К. Рабочее тело получает 1000 Дж за цикл. Найдите работу и КПД.',
         r'$\eta = 1 - T_2/T_1 = 25\%$, $A = 250$ Дж', 5, 'open'),
        ('Докажите, что КПД цикла Карно максимален для данных температур. Рассмотрите произвольный обратимый цикл.',
         'Доказательство через энтропию', 6, 'open'),
    ]),
]

# (last, first, middle, level)
# level: 'strong', 'medium', 'weak'
STUDENTS_9A = [
    ('Иванов', 'Алексей', 'Дмитриевич', 'medium'),
    ('Петрова', 'Мария', 'Сергеевна', 'medium'),
    ('Сидоров', 'Максим', 'Александрович', 'strong'),
    ('Козлова', 'Анна', 'Михайловна', 'strong'),
    ('Новиков', 'Дмитрий', 'Андреевич', 'strong'),
    ('Морозов', 'Кирилл', 'Николаевич', 'medium'),
    ('Волков', 'Матвей', 'Петрович', 'weak'),
    ('Соколова', 'Дарья', 'Владимировна', 'medium'),
    ('Лебедев', 'Артём', 'Игоревич', 'medium'),
    ('Кузнецова', 'Виктория', 'Сергеевна', 'medium'),
    ('Попов', 'Никита', 'Дмитриевич', 'medium'),
    ('Андреева', 'Елизавета', 'Александровна', 'weak'),
    ('Егоров', 'Егор', 'Николаевич', 'weak'),
    ('Медведева', 'Полина', 'Андреевна', 'weak'),
    ('Николаев', 'Данил', 'Михайлович', 'weak'),
]

STUDENTS_9B = [
    ('Фёдоров', 'Иван', 'Сергеевич', 'medium'),
    ('Михайлова', 'София', 'Дмитриевна', 'strong'),
    ('Зайцев', 'Тимур', 'Андреевич', 'medium'),
    ('Орлова', 'Ксения', 'Александровна', 'medium'),
    ('Белов', 'Артём', 'Петрович', 'strong'),
    ('Громова', 'Алиса', 'Михайловна', 'medium'),
    ('Степанов', 'Марк', 'Николаевич', 'weak'),
    ('Васильева', 'Полина', 'Игоревна', 'medium'),
    ('Титов', 'Даниил', 'Владимирович', 'medium'),
    ('Климова', 'Екатерина', 'Сергеевна', 'strong'),
    ('Романов', 'Глеб', 'Дмитриевич', 'medium'),
    ('Захарова', 'Валерия', 'Андреевна', 'weak'),
    ('Макаров', 'Илья', 'Николаевич', 'weak'),
    ('Панова', 'Алина', 'Михайловна', 'weak'),
    ('Борисов', 'Семён', 'Петрович', 'weak'),
]


class Command(BaseCommand):
    help = 'Создаёт полный набор тестовых данных'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Удалить все данные перед созданием')

    def handle(self, *args, **options):
        if options['clear']:
            self._clear()

        self.stdout.write('\n🌱 Создание тестовых данных...\n')

        academic_year = self._get_or_create_academic_year()
        topics = self._create_topics()
        all_tasks, tasks_by_group = self._create_tasks_and_groups(topics)
        students_9a, students_9b, grp_a, grp_b = self._create_students(academic_year)
        course = self._create_course(academic_year, grp_a, grp_b)

        # КР №1 (Механика) — группы 0-4
        work1, v1_tasks = self._create_kr(
            'КР №1: Механическое движение',
            tasks_by_group, group_indices=[0, 1, 2, 3, 4],
            num_variants=4,
        )
        # КР №2 (Тепловые) — группы 5-9
        work2, v2_tasks = self._create_kr(
            'КР №2: Тепловые явления',
            tasks_by_group, group_indices=[5, 6, 7, 8, 9],
            num_variants=4,
        )

        # События + оценки
        self._create_graded_event(
            'КР №1: Мех. движение — 9А',
            work1, v1_tasks, students_9a, course, days_ago=30,
        )
        self._create_graded_event(
            'КР №2: Тепловые — 9Б',
            work2, v2_tasks, students_9b, course, days_ago=14,
        )

        # Логи заданий
        all_students = (
            list(zip(students_9a, [l for *_, l in STUDENTS_9A])) +
            list(zip(students_9b, [l for *_, l in STUDENTS_9B]))
        )
        self._create_task_logs(all_students, tasks_by_group)

        self._print_summary()
        self.stdout.write(self.style.SUCCESS('\n✅ Тестовые данные созданы!\n'))

    # ─── Очистка ─────────────────────────────────
    def _clear(self):
        self.stdout.write('🗑️  Удаление данных...')
        Mark.objects.all().delete()
        EventParticipation.objects.all().delete()
        Event.objects.all().delete()
        StudentTaskLog.objects.all().delete()
        VariantTask.objects.all().delete()
        Variant.objects.all().delete()
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

    # ─── Academic Year ───────────────────────────
    def _get_or_create_academic_year(self):
        try:
            from core.models import AcademicYear
            ay, _ = AcademicYear.objects.get_or_create(
                name='2025-2026',
                defaults={'start_date': date(2025, 9, 1),
                          'end_date': date(2026, 6, 30),
                          'is_active': True}
            )
            self.stdout.write(f'  📅 Учебный год: {ay}')
            return ay
        except (ImportError, Exception) as e:
            self.stdout.write(f'  ⚠️ AcademicYear: {e}')
            return None

    # ─── Темы ────────────────────────────────────
    def _create_topics(self):
        topics = []
        for i, (name, section, desc) in enumerate(TOPICS_DATA, 1):
            t = Topic.objects.create(
                name=name,
                subject=SUBJECT,
                section=section,
                grade_level=GRADE,
                order=i,
                description=desc,
            )
            topics.append(t)

            # По 2 подтемы
            SubTopic.objects.create(
                topic=t, name=f'{name}: теория', order=1)
            SubTopic.objects.create(
                topic=t, name=f'{name}: задачи', order=2)

        self.stdout.write(f'  📚 Темы: {len(topics)}, подтем: {len(topics)*2}')
        return topics

    # ─── Задания + Группы ────────────────────────
    def _create_tasks_and_groups(self, topics):
        all_tasks = []
        tasks_by_group = []  # [(group_obj, [task_obj, ...]), ...]

        for grp_name, topic_idx, grp_diff, task_defs in GROUPS_DATA:
            topic = topics[topic_idx]
            group = AnalogGroup.objects.create(
                name=grp_name,
                difficulty=grp_diff,
            )
            group_tasks = []
            for text, answer, diff, ttype in task_defs:
                task = Task.objects.create(
                    text=text,
                    answer=answer,
                    difficulty=diff,
                    task_type=ttype,
                    topic=topic,
                    cognitive_level='apply' if diff <= 2 else 'analyze',
                )
                TaskGroup.objects.create(task=task, group=group)
                group_tasks.append(task)
                all_tasks.append(task)

            tasks_by_group.append((group, group_tasks))

        self.stdout.write(
            f'  📝 Задания: {len(all_tasks)}, групп: {len(tasks_by_group)}')
        return all_tasks, tasks_by_group

    # ─── Ученики ─────────────────────────────────
    def _create_students(self, academic_year):
        def create_list(data):
            result = []
            for last, first, middle, level in data:
                s = Student.objects.create(
                    last_name=last,
                    first_name=first,
                    middle_name=middle,
                )
                result.append(s)
            return result

        students_a = create_list(STUDENTS_9A)
        students_b = create_list(STUDENTS_9B)

        kwargs_a = {'name': '9А'}
        kwargs_b = {'name': '9Б'}
        if academic_year:
            kwargs_a['academic_year'] = academic_year
            kwargs_b['academic_year'] = academic_year

        grp_a = StudentGroup.objects.create(**kwargs_a)
        grp_a.students.set(students_a)
        grp_b = StudentGroup.objects.create(**kwargs_b)
        grp_b.students.set(students_b)

        self.stdout.write(
            f'  👨‍🎓 Ученики: {len(students_a)}+{len(students_b)}, '
            f'группы: {grp_a.name}, {grp_b.name}')
        return students_a, students_b, grp_a, grp_b

    # ─── Курс ────────────────────────────────────
    def _create_course(self, academic_year, grp_a, grp_b):
        kwargs = {
            'name': f'{SUBJECT} {GRADE} класс',
            'subject': SUBJECT,
            'grade_level': GRADE,
            'hours_per_week': 3,
            'is_active': True,
        }
        if academic_year:
            kwargs['year'] = academic_year

        course = Course.objects.create(**kwargs)
        course.student_groups.add(grp_a, grp_b)
        self.stdout.write(f'  📖 Курс: {course.name}')
        return course

    # ─── Контрольная работа ──────────────────────
    def _create_kr(self, name, tasks_by_group, group_indices, num_variants=4):
        """Создаёт КР с вариантами.
        Каждый вариант берёт по 1 заданию из каждой группы (разные задания).
        Возвращает (work, {variant_num: [task_obj, ...]})
        """
        groups = [tasks_by_group[i] for i in group_indices]
        tasks_per_variant = len(groups)

        # Считаем max_score: каждое задание = difficulty баллов
        # Берём первый вариант как эталон
        sample_score = sum(
            grp_tasks[0].difficulty for _, grp_tasks in groups
        )

        work = Work.objects.create(
            name=name,
            work_type='regular',
            max_score=sample_score * 2,
            duration=45,
        )

        variant_tasks_map = {}

        for v_num in range(1, num_variants + 1):
            variant = Variant.objects.create(
                work=work,
                number=v_num,
                work_name_snapshot=name,
                max_score_snapshot=0,
                variant_type='regular',
            )
            work.variant_counter = v_num
            work.save(update_fields=['variant_counter'])

            v_tasks = []
            total_score = 0
            for order, (group, grp_tasks) in enumerate(groups, 1):
                # Берём задание по индексу варианта (циклически)
                task_idx = (v_num - 1) % len(grp_tasks)
                task = grp_tasks[task_idx]
                weight = task.difficulty or 2
                VariantTask.objects.create(
                    variant=variant,
                    task=task,
                    order=order,
                    weight=float(weight),
                    max_points=weight * 2,  # каждое стоит difficulty*2 баллов
                )
                total_score += weight * 2
                v_tasks.append(task)

            variant.max_score_snapshot = total_score
            variant.save(update_fields=['max_score_snapshot'])
            variant_tasks_map[v_num] = v_tasks

        work.max_score = total_score
        work.save(update_fields=['max_score'])

        self.stdout.write(
            f'  📋 Работа: {name} ({num_variants} вар., '
            f'{tasks_per_variant} заданий, max={total_score})')
        return work, variant_tasks_map

    # ─── Событие с оценками ──────────────────────
    def _create_graded_event(self, name, work, variant_tasks_map,
                              students, course, days_ago):
        event_date = tz.now() - timedelta(days=days_ago)

        event = Event.objects.create(
            name=name,
            planned_date=event_date,
            actual_start=event_date,
            actual_end=event_date + timedelta(minutes=45),
            work=work,
            course=course,
            status='graded',
            description=f'Контрольная работа: {name}',
        )


        num_variants = len(variant_tasks_map)

        for i, student in enumerate(students):
            v_num = (i % num_variants) + 1
            variant = Variant.objects.get(work=work, number=v_num)
            v_tasks = variant_tasks_map[v_num]

            # Определяем уровень ученика
            level = self._get_student_level(student, students)

            ep = EventParticipation.objects.create(
                event=event,
                student=student,
                variant=variant,
                status='graded',
            )

            # Генерируем баллы по заданиям
            task_scores, total_pts, total_max = self._generate_scores(
                v_tasks, variant, level)

            # Оценка
            pct = total_pts / total_max * 100 if total_max else 0
            if pct >= 85:
                score = 5
            elif pct >= 65:
                score = 4
            elif pct >= 40:
                score = 3
            else:
                score = 2

            Mark.objects.create(
                participation=ep,
                score=score,
                points=total_pts,
                max_points=total_max,
                task_scores=task_scores,
            )

        self.stdout.write(
            f'  📊 Событие: {name} ({len(students)} учеников)')
        return event

    def _get_student_level(self, student, students_list):
        """Определяем уровень по исходным данным"""
        # Ищем в 9А
        for data_list in [STUDENTS_9A, STUDENTS_9B]:
            for j, (last, first, middle, level) in enumerate(data_list):
                if student.last_name == last and student.first_name == first:
                    return level
        return 'medium'

    def _generate_scores(self, tasks, variant, level):
        """Генерируем task_scores JSON с реалистичными баллами"""
        task_scores = {}
        total_pts = 0
        total_max = 0

        # Берём VariantTasks для получения max_points
        vt_list = VariantTask.objects.filter(variant=variant).order_by('order')

        for vt in vt_list:
            task = vt.task
            max_pts = int(vt.max_points)

            if level == 'strong':
                # 80-100%: обычно полный балл, иногда -1
                pts = max_pts if random.random() < 0.7 else max(0, max_pts - random.randint(0, 1))
            elif level == 'medium':
                # 50-80%: разброс
                pts = round(max_pts * random.uniform(0.4, 0.9))
            else:
                # 20-50%: часто 0 или мало
                pts = round(max_pts * random.uniform(0.0, 0.5))

            pts = max(0, min(pts, max_pts))

            task_scores[str(task.pk)] = {
                'points': pts,
                'max_points': max_pts,
                'comment': '',
            }
            total_pts += pts
            total_max += max_pts

        return task_scores, total_pts, total_max

    # ─── Логи заданий ────────────────────────────
    def _create_task_logs(self, all_students_with_levels, tasks_by_group):
        """Создаём StudentTaskLog для каждого ученика по каждой группе.
        Это имитирует историю: ученик решал задания из разных групп с разным успехом.
        """
        logs_count = 0

        for student, level in all_students_with_levels:
            for group, group_tasks in tasks_by_group:
                # Каждый ученик решал 1-3 задания из каждой группы
                n_tasks = random.randint(1, min(3, len(group_tasks)))
                sample = random.sample(group_tasks, n_tasks)

                for task in sample:
                    if level == 'strong':
                        pct = random.uniform(70, 100)
                    elif level == 'medium':
                        pct = random.uniform(40, 85)
                    else:
                        pct = random.uniform(10, 55)

                    max_pts = task.difficulty * 2 if task.difficulty else 2
                    earned = round(max_pts * pct / 100, 1)

                    StudentTaskLog.objects.create(
                        student=student,
                        task=task,
                        analog_group=group,
                        difficulty=task.difficulty or 2,
                        percentage=round(pct, 1),
                        points=Decimal(str(earned)),
                        max_points=Decimal(str(max_pts)),
                        is_correct=(pct >= 70),
                        completed_at=tz.now() - timedelta(
                            days=random.randint(1, 60)),
                    )

                    logs_count += 1

        self.stdout.write(f'  📈 Логи заданий: {logs_count}')

    # ─── Сводка ──────────────────────────────────
    def _print_summary(self):
        self.stdout.write('\n' + '═' * 50)
        self.stdout.write('  СВОДКА ТЕСТОВЫХ ДАННЫХ')
        self.stdout.write('═' * 50)
        self.stdout.write(f'  Тем:            {Topic.objects.count()}')
        self.stdout.write(f'  Заданий:        {Task.objects.count()}')
        self.stdout.write(f'  Групп аналогов: {AnalogGroup.objects.count()}')
        self.stdout.write(f'  Учеников:       {Student.objects.count()}')
        self.stdout.write(f'  Работ:          {Work.objects.count()}')
        self.stdout.write(f'  Вариантов:      {Variant.objects.count()}')
        self.stdout.write(f'  Событий:        {Event.objects.count()}')
        self.stdout.write(f'  Оценок:         {Mark.objects.count()}')
        self.stdout.write(f'  Логов заданий:  {StudentTaskLog.objects.count()}')
        self.stdout.write('═' * 50)
