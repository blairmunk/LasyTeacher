from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import Event, EventParticipation, Mark
from .models import ReviewSession, ReviewComment


class ReviewDashboardView(TemplateView):
    """Главная панель проверки работ"""
    template_name = 'review/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        events = Event.objects.annotate(
            total_participants=Count('eventparticipation'),
            graded_participants=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='graded')
            ),
            absent_participants=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='absent')
            ),
        ).filter(
            total_participants__gt=0
        ).select_related('work', 'course').order_by('-planned_date')

        needs_review = []
        in_progress = []
        fully_graded = []

        for event in events:
            active = event.total_participants - event.absent_participants
            graded = event.graded_participants

            if active > 0:
                progress = round(graded / active * 100, 1)
            else:
                progress = 100.0

            event_data = {
                'event': event,
                'total_participants': event.total_participants,
                'active_participants': active,
                'graded_participants': graded,
                'absent_participants': event.absent_participants,
                'progress_percentage': progress,
                'remaining': active - graded,
            }

            # Логика категоризации:
            # 1. Event.status принудительно влияет на категорию
            # 2. Прогресс участников — вторичный фактор
            
            event_status = getattr(event, 'status', '')
            
            if event_status in ('planned', 'in_progress'):
                # Событие ещё не проведено — ожидает
                needs_review.append(event_data)
            elif event_status == 'reviewing':
                # Статус "на проверке" — всегда в процессе,
                # даже если все участники уже оценены
                in_progress.append(event_data)
            elif event_status == 'completed':
                # Проведено, но не проверено
                if graded == 0:
                    needs_review.append(event_data)
                else:
                    in_progress.append(event_data)
            elif event_status == 'graded':
                # Полностью проверено
                if progress >= 100:
                    fully_graded.append(event_data)
                else:
                    # Статус graded, но не все проверены — коллизия
                    in_progress.append(event_data)
            else:
                # Без статуса — определяем по прогрессу
                if progress >= 100:
                    fully_graded.append(event_data)
                elif graded > 0:
                    in_progress.append(event_data)
                else:
                    needs_review.append(event_data)

        context.update({
            'needs_review': needs_review,
            'in_progress': in_progress,
            'fully_graded': fully_graded,
            'total_events': len(needs_review) + len(in_progress) + len(fully_graded),
        })

        if self.request.user.is_authenticated:
            context['recent_sessions'] = ReviewSession.objects.filter(
                reviewer=self.request.user
            ).select_related('event', 'event__work').order_by('-started_at')[:5]

        return context


class EventReviewView(DetailView):
    """Проверка конкретного события"""
    model = Event
    template_name = 'review/event_review.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        participations = event.eventparticipation_set.select_related(
            'student', 'variant'
        ).order_by('student__last_name', 'student__first_name')

        # Проверяем готовность
        total_count = participations.count()
        has_participants = total_count > 0
        variants_assigned = participations.filter(variant__isnull=False).exists()
        all_variants_assigned = has_participants and not participations.filter(
            variant__isnull=True
        ).exclude(status='absent').exists()

        context['has_participants'] = has_participants
        context['variants_assigned'] = variants_assigned
        context['all_variants_assigned'] = all_variants_assigned

        # Блокировка: нет учеников или нет вариантов
        if not has_participants:
            context['blocked'] = True
            context['block_reason'] = 'no_participants'
            return context

        if not variants_assigned:
            context['blocked'] = True
            context['block_reason'] = 'no_variants'
            return context

        context['blocked'] = False

        # Доступные варианты для inline-назначения
        if event.work:
            from works.models import Variant
            context['available_variants'] = Variant.objects.filter(
                work=event.work
            ).order_by('number')
        else:
            context['available_variants'] = []


        participations_data = []
        graded_count = 0
        absent_count = 0
        scores = []

        for p in participations:
            mark = Mark.objects.filter(participation=p).first()
            has_mark = mark is not None and mark.score is not None
            is_absent = p.status == 'absent'

            if has_mark:
                graded_count += 1
                scores.append(mark.score)
            if is_absent:
                absent_count += 1

            participations_data.append({
                'participation': p,
                'mark': mark,
                'has_mark': has_mark,
                'is_absent': is_absent,
                'student': p.student,
                'variant': p.variant,
            })

        active_participants = len(participations_data) - absent_count
        progress = round(
            graded_count / active_participants * 100, 1
        ) if active_participants > 0 else 100

        score_dist = {2: 0, 3: 0, 4: 0, 5: 0}
        for s in scores:
            if s in score_dist:
                score_dist[s] += 1

        context.update({
            'participations_data': participations_data,
            'total_participants': len(participations_data),
            'active_participants': active_participants,
            'graded_participants': graded_count,
            'absent_participants': absent_count,
            'progress_percentage': progress,
            'avg_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'score_distribution': score_dist,
        })

        if self.request.user.is_authenticated:
            session, _ = ReviewSession.objects.get_or_create(
                reviewer=self.request.user,
                event=event,
                defaults={
                    'total_participations': active_participants,
                    'checked_participations': graded_count,
                }
            )
            session.total_participations = active_participants
            session.checked_participations = graded_count
            session.save()
            context['review_session'] = session

        return context


class ParticipationReviewView(TemplateView):
    """Проверка работы ученика"""
    template_name = 'review/participation_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participation_id = kwargs.get('pk')

        participation = get_object_or_404(
            EventParticipation.objects.select_related(
                'student', 'variant', 'event', 'event__work'
            ),
            pk=participation_id
        )

        # Получаем или создаём оценку
        variant_tasks = list(
            participation.variant.tasks.all().select_related('topic')
        ) if participation.variant else []

        mark, created = Mark.objects.get_or_create(
            participation=participation,
            defaults={
                'max_points': len(variant_tasks) * 5,
            }
        )

        # Подготовка данных заданий с баллами
        tasks_with_scores = []
        existing_scores = mark.task_scores or {}

        for i, task in enumerate(variant_tasks):
            task_uuid = str(task.id)
            # Поддержка обоих форматов ключей
            task_data_old = existing_scores.get(task_uuid, {})
            task_data_new = existing_scores.get(f'task_{task_uuid}', {})
            task_data = task_data_new or task_data_old

            tasks_with_scores.append({
                'task': task,
                'number': i + 1,
                'points': task_data.get('points', 0),
                'max_points': task_data.get('max_points', 5),
                'comment': task_data.get('comment', ''),
            })

        context.update({
            'participation': participation,
            'mark': mark,
            'tasks_with_scores': tasks_with_scores,
            'typical_comments': ReviewComment.objects.filter(
                is_active=True
            ).order_by('-usage_count')[:10],
        })

        # Навигация между работами (пропускаем отсутствующих)
        all_participations = list(
            participation.event.eventparticipation_set.exclude(
                status='absent'
            ).select_related('student').order_by(
                'student__last_name', 'student__first_name'
            )
        )

        try:
            current_index = next(
                i for i, p in enumerate(all_participations) if p.pk == participation.pk
            )
        except StopIteration:
            current_index = 0

        total = len(all_participations)

        context.update({
            'previous_participation': (
                all_participations[current_index - 1] if current_index > 0 else None
            ),
            'next_participation': (
                all_participations[current_index + 1] if current_index < total - 1 else None
            ),
            'current_position': current_index + 1,
            'total_positions': total,
            'navigation_progress': round(
                (current_index + 1) / total * 100, 1
            ) if total > 0 else 0,
        })

        return context

    def post(self, request, pk):
        """Сохранение результатов проверки"""
        participation = get_object_or_404(EventParticipation, pk=pk)
        mark, _ = Mark.objects.get_or_create(participation=participation)

        # Оценка
        score = request.POST.get('score')
        if score:
            mark.score = int(score)

        # Баллы
        points = request.POST.get('points')
        if points:
            mark.points = int(points)
        max_points = request.POST.get('max_points')
        if max_points:
            mark.max_points = int(max_points)

        # Комментарии
        mark.teacher_comment = request.POST.get('teacher_comment', '')
        mark.mistakes_analysis = request.POST.get('mistakes_analysis', '')

        mark.checked_at = timezone.now()
        mark.checked_by = (
            request.user.get_full_name()
            if request.user.is_authenticated
            else 'Учитель'
        )

        # === Загрузка скана работы ===
        if 'work_scan' in request.FILES:
            uploaded_file = request.FILES['work_scan']

            # Валидация
            max_size = 10 * 1024 * 1024  # 10 МБ
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/webp',
            ]

            if uploaded_file.size > max_size:
                messages.warning(
                    request,
                    f'⚠️ Файл слишком большой ({uploaded_file.size // 1024 // 1024} МБ). '
                    f'Максимум 10 МБ.'
                )
            elif uploaded_file.content_type not in allowed_types:
                messages.warning(
                    request,
                    f'⚠️ Неподдерживаемый формат: {uploaded_file.content_type}. '
                    f'Допустимы: PDF, JPEG, PNG, WebP.'
                )
            else:
                # Удаляем старый файл если есть
                if mark.work_scan:
                    mark.work_scan.delete(save=False)
                mark.work_scan = uploaded_file

        # Детализация по заданиям
        task_scores = {}
        for key, value in request.POST.items():
            if key.startswith('task_') and '_max' not in key and '_comment' not in key:
                task_uuid = key[5:]  # убираем "task_"
                points_val = int(value) if value else 0
                max_val = int(request.POST.get(f'task_{task_uuid}_max', 5))
                comment_val = request.POST.get(f'task_{task_uuid}_comment', '')

                score_data = {
                    'points': points_val,
                    'max_points': max_val,
                    'comment': comment_val,
                }
                task_scores[task_uuid] = score_data
                task_scores[f'task_{task_uuid}'] = score_data

        mark.task_scores = task_scores
        mark.save()

        # Обновляем статус участия
        participation.status = 'graded'
        participation.graded_at = timezone.now()
        participation.save()

        # Синхронизация статуса события
        event = participation.event
        all_active = event.eventparticipation_set.exclude(status='absent')
        all_graded = all_active.filter(status='graded')

        if all_active.count() > 0 and all_active.count() == all_graded.count():
            event.status = 'graded'
            event.save()
        elif event.status not in ('reviewing', 'graded'):
            event.status = 'reviewing'
            event.save()

        # Имя ученика
        student = participation.student
        student_name = f'{student.last_name} {student.first_name}'

        # Сообщение об успехе
        scan_msg = ''
        if 'work_scan' in request.FILES and mark.work_scan:
            scan_msg = ' + скан загружен'
        messages.success(request, f'Работа {student_name} проверена (оценка: {mark.score}){scan_msg}')

        # Навигация
        if 'save_and_next' in request.POST:
            all_participations = list(
                participation.event.eventparticipation_set.exclude(
                    status='absent'
                ).order_by('student__last_name', 'student__first_name')
            )
            try:
                current_index = next(
                    i for i, p in enumerate(all_participations)
                    if p.pk == participation.pk
                )
            except StopIteration:
                current_index = -1

            next_p = None
            for i in range(current_index + 1, len(all_participations)):
                p = all_participations[i]
                if not Mark.objects.filter(
                    participation=p, score__isnull=False
                ).exists():
                    next_p = p
                    break

            if next_p is None and current_index + 1 < len(all_participations):
                next_p = all_participations[current_index + 1]

            if next_p:
                return redirect('review:participation-review', pk=next_p.pk)
            else:
                messages.info(request, '✅ Все работы проверены!')
                return redirect('review:event-review', pk=participation.event.pk)

        return redirect('review:event-review', pk=participation.event.pk)



def ajax_calculate_score(request):
    """AJAX расчёт оценки по баллам"""
    points = int(request.GET.get('points', 0))
    max_points = int(request.GET.get('max_points', 1))

    percentage = (points / max_points) * 100 if max_points > 0 else 0

    if percentage >= 85:
        score = 5
    elif percentage >= 70:
        score = 4
    elif percentage >= 50:
        score = 3
    else:
        score = 2

    return JsonResponse({
        'score': score,
        'percentage': round(percentage, 1)
    })

from django.views.decorators.http import require_POST

@require_POST
def finalize_event(request, pk):
    """Завершить проверку события — установить статус graded"""
    event = get_object_or_404(Event, pk=pk)
    event.status = 'graded'
    event.save()
    messages.success(request, f'✅ Проверка завершена: {event.name}')
    return redirect('review:event-review', pk=event.pk)

@require_POST
def toggle_absent(request, pk):
    """Переключить статус отсутствия"""
    participation = get_object_or_404(EventParticipation, pk=pk)

    if participation.status == 'absent':
        participation.status = 'assigned'
        messages.info(request, f'{participation.student.last_name} — статус снят')
    else:
        participation.status = 'absent'
        messages.warning(request, f'{participation.student.last_name} — отсутствовал')

    participation.save()

    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('review:event-review', pk=participation.event.pk)