"""Build a replaceable, idempotent teaching scenario from JSON."""

import json
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from core.models import AcademicYear
from core_logic.interfaces.work_repo import (
    WorkContentBlockParams,
    WorkTaskSelectionParams,
)
from core_logic.use_cases.grade_student_work import GradeStudentWorkRequest
from core_logic.use_cases.save_work import SaveWorkSpecificationRequest
from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from document_engine.models import PrintSettings
from events.models import Event, EventParticipation
from infrastructure.container import container
from site_settings.models import SiteSettings
from students.models import StudentGroup, StudentTaskLog
from task_groups.models import AnalogGroup
from works.models import Variant, Work


DEFAULT_MANIFEST = Path('data/test_scenario.json')


class Command(BaseCommand):
    help = 'Создать идемпотентный учебный тестовый сценарий из JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'manifest',
            nargs='?',
            default=str(DEFAULT_MANIFEST),
            help='Путь к JSON manifest сценария',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить сценарий без сохранения',
        )

    def handle(self, *args, **options):
        manifest_path = Path(options['manifest'])
        if not manifest_path.exists():
            raise CommandError(f'Manifest не найден: {manifest_path}')

        manifest = self._read_manifest(manifest_path)
        self.namespace = self._read_namespace(manifest)
        self.academic_year = self._get_academic_year(manifest)
        self.stats = {
            'courses': 0,
            'works': 0,
            'variants': 0,
            'events': 0,
            'participations': 0,
            'marks': 0,
        }

        with transaction.atomic():
            self._remove_previous_scenario(manifest)
            self._configure_site(manifest)
            self._update_topic_content(manifest)
            profiles = self._build_print_profiles(manifest)
            courses = self._build_courses(manifest)
            works = self._build_works(manifest, courses)
            self._build_events(manifest, courses, works)

            if options['dry_run']:
                transaction.set_rollback(True)

        summary = ', '.join(
            f'{name}={count}'
            for name, count in self.stats.items()
        )
        self.stdout.write(f'Тестовый сценарий: {summary}')
        if profiles:
            self.stdout.write(f'Профилей оформления: {len(profiles)}')
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN: изменения не сохранены.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('Тестовый сценарий готов.'))

    @staticmethod
    def _read_manifest(path):
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as error:
            raise CommandError(f'Некорректный JSON: {error}') from error

    @staticmethod
    def _read_namespace(manifest):
        namespace = manifest.get('namespace')
        if not namespace:
            raise CommandError('В manifest отсутствует namespace.')
        try:
            return uuid.UUID(namespace)
        except ValueError as error:
            raise CommandError('namespace должен быть UUID.') from error

    @staticmethod
    def _get_academic_year(manifest):
        year_name = manifest.get('academic_year')
        if not year_name:
            raise CommandError('В manifest отсутствует academic_year.')
        academic_year = AcademicYear.objects.filter(name=year_name).first()
        if academic_year is None:
            raise CommandError(
                f'Учебный год {year_name} не найден. '
                'Сначала импортируйте классы и учеников.'
            )
        return academic_year

    def _scenario_id(self, kind, key):
        if not key:
            raise CommandError(f'Для {kind} не указан key.')
        return uuid.uuid5(self.namespace, f'{kind}:{key}')

    def _remove_previous_scenario(self, manifest):
        event_ids = [
            self._scenario_id('event', item.get('key'))
            for item in manifest.get('events', [])
        ]
        work_ids = [
            self._scenario_id('work', item.get('key'))
            for item in manifest.get('works', [])
        ]
        StudentTaskLog.objects.filter(event_id__in=event_ids).delete()
        Event.objects.filter(pk__in=event_ids).delete()
        Variant.objects.filter(work_id__in=work_ids).delete()

    def _configure_site(self, manifest):
        settings_data = manifest.get('site_settings', {})
        settings = SiteSettings.get()
        for field in (
            'school_name',
            'teacher_name',
            'default_subject',
            'points_scale',
            'default_variants_count',
            'pdf_font_size',
            'pdf_margin_top',
            'pdf_margin_bottom',
        ):
            if field in settings_data:
                setattr(settings, field, settings_data[field])
        settings.current_academic_year = self.academic_year.name
        settings.save()

        if not self.academic_year.is_active:
            self.academic_year.is_active = True
            self.academic_year.save()

    def _update_topic_content(self, manifest):
        for topic_data in manifest.get('topic_content', []):
            topic = self._get_topic(topic_data)
            topic.description = topic_data.get(
                'description',
                topic.description,
            )
            topic.save(update_fields=['description', 'updated_at'])
            for subtopic_name, content in topic_data.get(
                'subtopics',
                {},
            ).items():
                updated = SubTopic.objects.filter(
                    topic=topic,
                    name=subtopic_name,
                ).update(description=content)
                if not updated:
                    raise CommandError(
                        f'Подтема не найдена: {topic.name} / {subtopic_name}'
                    )

    def _build_print_profiles(self, manifest):
        profiles = {}
        for data in manifest.get('print_profiles', []):
            profile_id = self._scenario_id('print-profile', data.get('key'))
            profile, _ = PrintSettings.objects.update_or_create(
                id=profile_id,
                defaults={
                    'name': data['name'],
                    'description': data.get('description', ''),
                    'document_type': data.get('document_type', 'work'),
                    'custom_css': data.get('custom_css', ''),
                    'custom_latex_preamble': data.get(
                        'custom_latex_preamble',
                        '',
                    ),
                    'html_template_override': data.get(
                        'html_template_override',
                        '',
                    ),
                    'latex_template_override': data.get(
                        'latex_template_override',
                        '',
                    ),
                    'is_default': data.get('is_default', False),
                    'is_public': data.get('is_public', True),
                },
            )
            profile.full_clean()
            profiles[data['key']] = profile
        return profiles

    def _build_courses(self, manifest):
        courses = {}
        for data in manifest.get('courses', []):
            course_id = self._scenario_id('course', data.get('key'))
            course, _ = Course.objects.update_or_create(
                id=course_id,
                defaults={
                    'name': data['name'],
                    'description': data.get('description', ''),
                    'subject': data.get('subject', 'Физика'),
                    'grade_level': data['grade_level'],
                    'academic_year': self.academic_year.name,
                    'year': self.academic_year,
                    'start_date': self._optional_date(
                        data.get('start_date')
                    ),
                    'end_date': self._optional_date(data.get('end_date')),
                    'total_hours': data.get('total_hours'),
                    'hours_per_week': data.get('hours_per_week', 2),
                    'is_active': data.get('is_active', True),
                },
            )
            groups = [
                self._get_student_group(group_name)
                for group_name in data.get('student_groups', [])
            ]
            course.student_groups.set(groups)
            courses[data['key']] = course
            self.stats['courses'] += 1
        return courses

    def _build_works(self, manifest, courses):
        works = {}
        for data in manifest.get('works', []):
            work_id = self._scenario_id('work', data.get('key'))
            work, _ = Work.objects.update_or_create(
                id=work_id,
                defaults={
                    'name': data['name'],
                    'duration': data.get('duration', 45),
                    'variant_counter': 0,
                    'work_type': data.get('work_type', 'test'),
                    'max_score': data.get('max_score', 0),
                },
            )
            result = container.save_work_specification_use_case().execute(
                SaveWorkSpecificationRequest(
                    work_id=str(work.pk),
                    specs=[
                        self._work_spec(spec)
                        for spec in data.get('specification', [])
                    ],
                    content_blocks=[
                        self._content_block(block)
                        for block in data.get('content_blocks', [])
                    ],
                )
            )
            if result.status != 'saved':
                raise CommandError(
                    f'Не удалось сохранить работу {work.name}: '
                    + '; '.join(result.errors)
                )

            variant_count = data.get('variant_count', 0)
            if variant_count:
                compose_result = (
                    container.compose_work_variants_use_case().execute(
                        self._compose_request(str(work.pk), variant_count)
                    )
                )
                if compose_result.status != 'generated':
                    raise CommandError(
                        f'Не удалось создать варианты {work.name}: '
                        f'{compose_result.status}'
                    )
                self.stats['variants'] += compose_result.created_count

            assignment = data.get('course_assignment')
            if assignment:
                course = self._by_key(
                    courses,
                    assignment.get('course'),
                    'курс',
                )
                CourseAssignment.objects.update_or_create(
                    course=course,
                    work=work,
                    defaults={
                        'order': assignment.get('order', 1),
                        'planned_date': self._optional_date(
                            assignment.get('planned_date')
                        ),
                        'weight': assignment.get('weight', 1.0),
                    },
                )
            works[data['key']] = work
            self.stats['works'] += 1
        return works

    @staticmethod
    def _compose_request(work_id, count):
        from core_logic.use_cases.compose_work_variants import (
            ComposeWorkVariantsRequest,
        )

        return ComposeWorkVariantsRequest(work_id=work_id, count=count)

    def _work_spec(self, data):
        group = self._get_analog_group(data)
        return WorkTaskSelectionParams(
            analog_group_id=str(group.pk),
            order=data['order'],
            count=data.get('count', 1),
            weight=data.get('weight', 1),
            bank_role_filter=data.get('bank_role_filter', 'any'),
            render_mode=data.get('render_mode', 'task_only'),
            is_assessable=data.get('is_assessable', True),
            blank_cells_after=data.get('blank_cells_after', False),
            blank_cells_rows=data.get('blank_cells_rows', 6),
        )

    def _content_block(self, data):
        return WorkContentBlockParams(
            content_type=data['content_type'],
            order=data['order'],
            title=data.get('title', ''),
            body=data.get('body', ''),
            topic_ids=[
                str(self._get_topic(topic_ref).pk)
                for topic_ref in data.get('topics', [])
            ],
            include_subtopics=data.get('include_subtopics', False),
        )

    def _build_events(self, manifest, courses, works):
        for data in manifest.get('events', []):
            work = self._by_key(works, data.get('work'), 'работа')
            course = (
                self._by_key(courses, data.get('course'), 'курс')
                if data.get('course')
                else None
            )
            planned_at = self._required_datetime(data.get('planned_date'))
            event = Event.objects.create(
                id=self._scenario_id('event', data.get('key')),
                name=data['name'],
                work=work,
                course=course,
                planned_date=planned_at,
                status=data.get('status', 'planned'),
                location=data.get('location', ''),
                description=data.get('description', ''),
                actual_start=self._event_actual_start(data, planned_at),
                actual_end=self._event_actual_end(data, planned_at),
            )
            students = list(
                self._get_student_group(
                    data['student_group']
                ).students.all().order_by('last_name', 'first_name')
            )
            limit = data.get('participant_limit')
            if limit:
                students = students[:limit]
            self._populate_event(event, students, data)
            self.stats['events'] += 1

    def _populate_event(self, event, students, data):
        variants = list(
            Variant.objects.filter(work=event.work).order_by('number')
        )
        if not variants:
            raise CommandError(
                f'У работы события {event.name} нет вариантов.'
            )

        participant_use_case = container.add_event_participants_use_case()
        participant_use_case.execute(
            self._participants_request(
                str(event.pk),
                [str(student.pk) for student in students],
            )
        )
        participations = list(
            EventParticipation.objects.filter(event=event).order_by(
                'student__last_name',
                'student__first_name',
            )
        )
        assignments = {
            str(participation.pk): str(variants[index % len(variants)].pk)
            for index, participation in enumerate(participations)
        }
        container.assign_event_variants_use_case().execute(
            self._assignments_request(str(event.pk), assignments)
        )
        for participation in participations:
            participation.refresh_from_db()

        absent_indexes = set(data.get('absent_indexes', []))
        graded_count = data.get(
            'graded_count',
            len(participations) if data.get('status') == 'graded' else 0,
        )
        for index, participation in enumerate(participations):
            if index in absent_indexes:
                participation.status = 'absent'
                participation.save(update_fields=['status', 'updated_at'])
                continue
            if index < graded_count:
                self._grade_participation(participation, index)
                continue
            self._set_participation_state(
                participation,
                event_status=data.get('status', 'planned'),
                planned_at=event.planned_date,
                index=index,
            )
        self.stats['participations'] += len(participations)

    @staticmethod
    def _participants_request(event_id, student_ids):
        from core_logic.use_cases.add_event_participants import (
            AddEventParticipantsRequest,
        )

        return AddEventParticipantsRequest(
            event_id=event_id,
            student_ids=student_ids,
        )

    @staticmethod
    def _assignments_request(event_id, assignments):
        from core_logic.use_cases.assign_event_variants import (
            AssignEventVariantsRequest,
        )

        return AssignEventVariantsRequest(
            event_id=event_id,
            assignments=assignments,
        )

    def _grade_participation(self, participation, student_index):
        task_scores = {}
        total_points = 0
        max_points = 0
        for variant_task in participation.variant.varianttask_set.filter(
            is_assessable=True,
        ).select_related('task').order_by('order'):
            available = variant_task.max_points
            deduction = (
                1
                if available and (student_index + variant_task.order) % 4 == 0
                else 0
            )
            points = max(available - deduction, 0)
            task_scores[str(variant_task.pk)] = {
                'variant_task_id': str(variant_task.pk),
                'task_id': str(variant_task.task_id),
                'points': points,
                'max_points': available,
                'comment': (
                    'Проверить ход решения.'
                    if points < available
                    else ''
                ),
            }
            total_points += points
            max_points += available
        percentage = (
            total_points / max_points * 100
            if max_points
            else 0
        )
        score = 5 if percentage >= 85 else 4 if percentage >= 70 else 3
        container.grade_student_work_use_case().execute(
            GradeStudentWorkRequest(
                participation_id=str(participation.pk),
                score=score,
                task_scores=task_scores,
                teacher_comment='Тестовая проверенная работа.',
                mistakes_analysis=(
                    'Автоматически созданный пример анализа ошибок.'
                ),
                recommendations='Повторить задания с потерянными баллами.',
                checked_by_display_name='Тестовый учитель',
                needs_attention=score <= 3,
                is_excellent=score == 5,
                sync_event_status=False,
            )
        )
        self.stats['marks'] += 1

    @staticmethod
    def _set_participation_state(
        participation,
        event_status,
        planned_at,
        index,
    ):
        fields = ['status', 'updated_at']
        if event_status in ('completed', 'reviewing', 'graded'):
            participation.status = 'completed'
            participation.started_at = planned_at + timedelta(minutes=index)
            participation.completed_at = (
                participation.started_at + timedelta(minutes=40)
            )
            fields.extend(['started_at', 'completed_at'])
        elif event_status == 'in_progress' and index < 5:
            participation.status = 'started'
            participation.started_at = planned_at + timedelta(minutes=index)
            fields.append('started_at')
        else:
            participation.status = 'assigned'
        participation.save(update_fields=fields)

    def _get_student_group(self, name):
        group = StudentGroup.objects.filter(
            name=name,
            academic_year=self.academic_year,
        ).first()
        if group is None:
            raise CommandError(
                f'Класс {name} ({self.academic_year.name}) не найден.'
            )
        return group

    @staticmethod
    def _get_analog_group(data):
        group = None
        if data.get('analog_group_id'):
            group = AnalogGroup.objects.filter(
                pk=data['analog_group_id']
            ).first()
        if group is None and data.get('analog_group'):
            group = AnalogGroup.objects.filter(
                name=data['analog_group']
            ).first()
        if group is None:
            raise CommandError(
                'Группа аналогов не найдена: '
                f"{data.get('analog_group_id') or data.get('analog_group')}"
            )
        return group

    @staticmethod
    def _get_topic(data):
        filters = {
            'name': data['name'],
            'grade_level': data['grade_level'],
        }
        if data.get('subject'):
            filters['subject'] = data['subject']
        topic = Topic.objects.filter(**filters).first()
        if topic is None:
            raise CommandError(
                f"Тема не найдена: {data['name']}, {data['grade_level']} класс"
            )
        return topic

    @staticmethod
    def _by_key(objects, key, label):
        try:
            return objects[key]
        except KeyError as error:
            raise CommandError(
                f'Неизвестная ссылка на {label}: {key}'
            ) from error

    @staticmethod
    def _optional_date(value):
        if not value:
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise CommandError(f'Некорректная дата: {value}')
        return parsed

    @staticmethod
    def _required_datetime(value):
        if not value:
            raise CommandError('Для события обязательна planned_date.')
        parsed = parse_datetime(value)
        if parsed is None:
            parsed_date = parse_date(value)
            if parsed_date:
                parsed = datetime.combine(parsed_date, time(hour=9))
        if parsed is None:
            raise CommandError(f'Некорректная дата и время: {value}')
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed)
        return parsed

    @staticmethod
    def _event_actual_start(data, planned_at):
        if data.get('status') == 'planned':
            return None
        return planned_at

    @staticmethod
    def _event_actual_end(data, planned_at):
        if data.get('status') not in (
            'completed',
            'reviewing',
            'graded',
            'closed',
        ):
            return None
        return planned_at + timedelta(minutes=data.get('duration', 45))
