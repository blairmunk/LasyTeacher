from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from events.models import Event, EventParticipation, Mark
from .models import ReviewSession


class ReviewDashboardView(TemplateView):
    """Главная панель проверки работ"""
    template_name = 'review/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from infrastructure.container import container

        dashboard = container.get_review_dashboard_use_case().execute()

        context.update({
            'needs_review': dashboard.needs_review,
            'in_progress': dashboard.in_progress,
            'fully_graded': dashboard.fully_graded,
            'total_events': dashboard.total_events,
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

        from infrastructure.container import container

        review_data = container.get_event_review_use_case().execute(str(event.pk))
        context.update({
            'has_participants': review_data.has_participants,
            'variants_assigned': review_data.variants_assigned,
            'all_variants_assigned': review_data.all_variants_assigned,
            'blocked': review_data.blocked,
            'block_reason': review_data.block_reason,
            'available_variants': review_data.available_variants,
            'participations_data': review_data.participations_data,
            'total_participants': review_data.total_participants,
            'active_participants': review_data.active_participants,
            'graded_participants': review_data.graded_participants,
            'absent_participants': review_data.absent_participants,
            'progress_percentage': review_data.progress_percentage,
            'avg_score': review_data.avg_score,
            'score_distribution': review_data.score_distribution,
        })

        if self.request.user.is_authenticated:
            session, _ = ReviewSession.objects.get_or_create(
                reviewer=self.request.user,
                event=event,
                defaults={
                    'total_participations': review_data.active_participants,
                    'checked_participations': review_data.graded_participants,
                }
            )
            session.total_participations = review_data.active_participants
            session.checked_participations = review_data.graded_participants
            session.save()
            context['review_session'] = session

        return context


class ParticipationReviewView(TemplateView):
    """Проверка работы ученика"""
    template_name = 'review/participation_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participation_id = kwargs.get('pk')
        from infrastructure.container import container

        review_data = container.get_participation_review_use_case().execute(
            str(participation_id),
        )

        context.update({
            'participation': review_data.participation,
            'mark': review_data.mark,
            'tasks_with_scores': review_data.tasks_with_scores,
            'typical_comments': review_data.typical_comments,
            'previous_participation': review_data.previous_participation,
            'next_participation': review_data.next_participation,
            'current_position': review_data.current_position,
            'total_positions': review_data.total_positions,
            'navigation_progress': review_data.navigation_progress,
        })

        return context

    def post(self, request, pk):
        """Сохранение результатов проверки"""
        participation = get_object_or_404(EventParticipation, pk=pk)

        # === Загрузка скана работы ===
        uploaded_file = None
        if 'work_scan' in request.FILES:
            candidate_file = request.FILES['work_scan']

            # Валидация
            max_size = 10 * 1024 * 1024  # 10 МБ
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/webp',
            ]

            if candidate_file.size > max_size:
                messages.warning(
                    request,
                    f'⚠️ Файл слишком большой ({candidate_file.size // 1024 // 1024} МБ). '
                    f'Максимум 10 МБ.'
                )
            elif candidate_file.content_type not in allowed_types:
                messages.warning(
                    request,
                    f'⚠️ Неподдерживаемый формат: {candidate_file.content_type}. '
                    f'Допустимы: PDF, JPEG, PNG, WebP.'
                )
            else:
                uploaded_file = candidate_file

        # Детализация по заданиям
        task_scores = {}
        for key, value in request.POST.items():
            if key.startswith('task_') and '_max' not in key and '_comment' not in key:
                task_uuid = key[5:]
                points_val = int(value) if value else 0
                max_val = int(request.POST.get(f'task_{task_uuid}_max', 5))
                comment_val = request.POST.get(f'task_{task_uuid}_comment', '')
                score_data = {
                    'points': points_val,
                    'max_points': max_val,
                    'comment': comment_val,
                }
                task_scores[task_uuid] = score_data

        from core_logic.use_cases.grade_student_work import GradeStudentWorkRequest
        from infrastructure.container import container

        def _int_or_none(value):
            return int(value) if value not in (None, '') else None

        result = container.grade_student_work_use_case().execute(
            GradeStudentWorkRequest(
                participation_id=str(participation.pk),
                score=_int_or_none(request.POST.get('score')),
                points=_int_or_none(request.POST.get('points')),
                max_points=_int_or_none(request.POST.get('max_points')),
                teacher_comment=request.POST.get('teacher_comment', ''),
                mistakes_analysis=request.POST.get('mistakes_analysis', ''),
                recommendations=request.POST.get('recommendations', ''),
                checked_by_display_name=(
                    request.user.get_full_name()
                    if request.user.is_authenticated
                    else ''
                ),
                checked_by_username=(
                    request.user.username
                    if request.user.is_authenticated
                    else ''
                ),
                work_scan=uploaded_file,
                task_scores=task_scores,
            )
        )

        # Сообщение об успехе
        scan_msg = ''
        if uploaded_file is not None:
            scan_msg = ' + скан загружен'
        messages.success(
            request,
            f'Работа {result.student_name} проверена (оценка: {result.score}){scan_msg}',
        )

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
    from core_logic.use_cases.calculate_review_score import (
        CalculateReviewScoreRequest,
    )
    from infrastructure.container import container

    result = container.calculate_review_score_use_case().execute(
        CalculateReviewScoreRequest(
            points=request.GET.get('points', 0),
            max_points=request.GET.get('max_points', 1),
        )
    )
    return JsonResponse({
        'score': result.score,
        'percentage': result.percentage,
    })

from django.views.decorators.http import require_POST

@require_POST
def finalize_event(request, pk):
    """Завершить проверку события — установить статус graded"""
    from core_logic.use_cases.finalize_review_event import (
        FinalizeReviewEventRequest,
    )
    from infrastructure.container import container

    event = container.finalize_review_event_use_case().execute(
        FinalizeReviewEventRequest(event_id=str(pk))
    )
    messages.success(request, f'✅ Проверка завершена: {event.name}')
    return redirect('review:event-review', pk=event.pk)

@require_POST
def toggle_absent(request, pk):
    """Переключить статус отсутствия"""
    from core_logic.use_cases.toggle_participation_absent import (
        ToggleParticipationAbsentRequest,
    )
    from infrastructure.container import container

    result = container.toggle_participation_absent_use_case().execute(
        ToggleParticipationAbsentRequest(participation_id=str(pk))
    )

    if result.is_absent:
        messages.warning(request, f'{result.student_last_name} — отсутствовал')
    else:
        messages.info(request, f'{result.student_last_name} — статус снят')

    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('review:event-review', pk=result.event_id)
