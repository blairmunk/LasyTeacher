from django.shortcuts import redirect
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from events.models import Event
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
        from core_logic.use_cases.get_review_save_navigation import (
            GetReviewSaveNavigationRequest,
        )
        from core_logic.use_cases.grade_student_work import GradeStudentWorkRequest
        from core_logic.use_cases.prepare_participation_review_submission import (
            PrepareParticipationReviewSubmissionRequest,
        )
        from core_logic.use_cases.validate_review_work_scan import (
            ValidateReviewWorkScanRequest,
        )
        from infrastructure.container import container

        participation_id = str(pk)
        submission = container.prepare_participation_review_submission_use_case().execute(
            PrepareParticipationReviewSubmissionRequest(data=request.POST),
        )

        uploaded_file = None
        if 'work_scan' in request.FILES:
            candidate_file = request.FILES['work_scan']
            file_validation = container.validate_review_work_scan_use_case().execute(
                ValidateReviewWorkScanRequest(
                    size=candidate_file.size,
                    content_type=candidate_file.content_type,
                )
            )
            if file_validation.accepted:
                uploaded_file = candidate_file
            else:
                messages.warning(request, file_validation.warning)

        result = container.grade_student_work_use_case().execute(
            GradeStudentWorkRequest(
                participation_id=participation_id,
                score=submission.score,
                points=submission.points,
                max_points=submission.max_points,
                teacher_comment=submission.teacher_comment,
                mistakes_analysis=submission.mistakes_analysis,
                recommendations=submission.recommendations,
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
                task_scores=submission.task_scores,
            )
        )

        scan_msg = ''
        if uploaded_file is not None:
            scan_msg = ' + скан загружен'
        messages.success(
            request,
            f'Работа {result.student_name} проверена (оценка: {result.score}){scan_msg}',
        )

        if 'save_and_next' in request.POST:
            navigation = container.get_review_save_navigation_use_case().execute(
                GetReviewSaveNavigationRequest(participation_id=participation_id),
            )
            if navigation.next_participation:
                return redirect(
                    'review:participation-review',
                    pk=navigation.next_participation.pk,
                )
            if navigation.all_checked:
                messages.info(request, '✅ Все работы проверены!')
            return redirect('review:event-review', pk=navigation.event_id)

        return redirect('review:event-review', pk=result.event_id)



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
