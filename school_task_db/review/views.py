from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from datetime import datetime

from events.models import Event, EventParticipation, Mark
from .models import ReviewSession, ReviewComment

class ReviewDashboardView(TemplateView):
    """Главная панель проверки работ"""
    template_name = 'review/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # События требующие проверки
        events_to_review = Event.objects.filter(
            status__in=['completed', 'reviewing']
        ).annotate(
            total_participants=Count('eventparticipation'),
            graded_participants=Count('eventparticipation', 
                                    filter=Q(eventparticipation__mark__isnull=False))
        ).order_by('-planned_date')
        
        # Группируем по статусам
        completed_events = []
        reviewing_events = []
        
        for event in events_to_review:
            progress_percentage = round(
                (event.graded_participants / event.total_participants * 100) 
                if event.total_participants > 0 else 0, 1
            )
            
            event_data = {
                'event': event,
                'total_participants': event.total_participants,
                'graded_participants': event.graded_participants,
                'progress_percentage': progress_percentage
            }
            
            if event.status == 'completed':
                completed_events.append(event_data)
            else:
                reviewing_events.append(event_data)
        
        context.update({
            'completed_events': completed_events,
            'reviewing_events': reviewing_events,
            'total_events_to_review': len(completed_events) + len(reviewing_events),
        })
        
        # Статистика проверяющего
        if self.request.user.is_authenticated:
            recent_sessions = ReviewSession.objects.filter(
                reviewer=self.request.user
            ).order_by('-started_at')[:5]
            context['recent_sessions'] = recent_sessions
        
        return context

class EventReviewView(DetailView):
    """Интерфейс проверки конкретного события"""
    model = Event
    template_name = 'review/event_review.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        
        # Все участники события с информацией о проверке
        participations = event.eventparticipation_set.select_related(
            'student', 'variant'
        ).order_by('student__last_name')
        
        # Добавляем информацию о статусе проверки
        participations_data = []
        graded_count = 0
        
        for participation in participations:
            try:
                mark = Mark.objects.get(participation=participation)
                has_mark = True
                graded_count += 1
            except Mark.DoesNotExist:
                mark = None
                has_mark = False
            
            participations_data.append({
                'participation': participation,
                'mark': mark,
                'has_mark': has_mark,
                'student': participation.student,
                'variant': participation.variant,
            })
        
        total_participants = len(participations_data)
        progress_percentage = round(
            (graded_count / total_participants * 100) if total_participants > 0 else 0, 1
        )
        
        context.update({
            'participations_data': participations_data,
            'total_participants': total_participants,
            'graded_participants': graded_count,
            'progress_percentage': progress_percentage,  # ДОБАВЛЕНО
        })
        
        # Создаем или получаем сессию проверки
        if self.request.user.is_authenticated:
            session, created = ReviewSession.objects.get_or_create(
                reviewer=self.request.user,
                event=event,
                defaults={
                    'total_participations': total_participants,
                    'checked_participations': graded_count
                }
            )
            # Обновляем статистику сессии
            session.total_participations = total_participants
            session.checked_participations = graded_count
            session.save()
            
            context['review_session'] = session
        
        return context

class ParticipationReviewView(TemplateView):
    """Проверка отдельной работы ученика"""
    template_name = 'review/participation_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participation_id = kwargs.get('pk')
        
        participation = get_object_or_404(
            EventParticipation.objects.select_related(
                'student', 'variant', 'event'
            ).prefetch_related('variant__tasks'),
            pk=participation_id
        )
        
        # Получаем или создаем отметку
        mark, created = Mark.objects.get_or_create(
            participation=participation,
            defaults={
                'max_points': participation.variant.tasks.count() * 5 if participation.variant else 20
            }
        )
        
        # ДОБАВЛЕНО: Подготавливаем данные для заданий с баллами
        tasks_with_scores = []
        if participation.variant:
            for task in participation.variant.tasks.all():
                task_key = f"task_{task.id}"
                task_data = {
                    'task': task,
                    'points': 0,
                    'max_points': 5,
                    'comment': ''
                }
                
                # Извлекаем данные из task_scores если они есть
                if mark.task_scores and task_key in mark.task_scores:
                    task_score_data = mark.task_scores[task_key]
                    task_data['points'] = task_score_data.get('points', 0)
                    task_data['max_points'] = task_score_data.get('max_points', 5)
                    task_data['comment'] = task_score_data.get('comment', '')
                
                tasks_with_scores.append(task_data)
        
        context.update({
            'participation': participation,
            'mark': mark,
            'tasks_with_scores': tasks_with_scores,  # НОВОЕ: готовые данные для шаблона
            'typical_comments': ReviewComment.objects.filter(is_active=True)
        })
        
        # Информация о следующей/предыдущей работе для навигации
        event_participations = participation.event.eventparticipation_set.order_by('student__last_name')
        participations_list = list(event_participations)
        
        try:
            current_index = participations_list.index(participation)
        except ValueError:
            current_index = 0
        
        # Вычисляем процент для навигации
        navigation_progress = round((current_index + 1) / len(participations_list) * 100, 1)
        
        context.update({
            'previous_participation': participations_list[current_index - 1] if current_index > 0 else None,
            'next_participation': participations_list[current_index + 1] if current_index < len(participations_list) - 1 else None,
            'current_position': current_index + 1,
            'total_positions': len(participations_list),
            'navigation_progress': navigation_progress,
        })
        
        return context
    
    def post(self, request, pk):
        """Сохранение результатов проверки"""
        participation = get_object_or_404(EventParticipation, pk=pk)
        mark, created = Mark.objects.get_or_create(participation=participation)
        
        # Обновляем отметку
        score = request.POST.get('score')
        if score:
            mark.score = int(score)
        
        points = request.POST.get('points')
        if points:
            mark.points = int(points)
            
        max_points = request.POST.get('max_points')
        if max_points:
            mark.max_points = int(max_points)
            
        mark.teacher_comment = request.POST.get('teacher_comment', '')
        mark.mistakes_analysis = request.POST.get('mistakes_analysis', '')
        mark.checked_at = datetime.now()
        mark.checked_by = request.user.get_full_name() if request.user.is_authenticated else 'Система'
        
        # Обработка детализации по заданиям
        task_scores = {}
        for key, value in request.POST.items():
            if key.startswith('task_') and not key.endswith('_max') and not key.endswith('_comment'):
                task_id = key.split('_')[1]
                points_value = int(value) if value else 0
                max_points_value = int(request.POST.get(f'task_{task_id}_max', 5))
                comment_value = request.POST.get(f'task_{task_id}_comment', '')
                
                task_scores[f"task_{task_id}"] = {
                    "points": points_value,
                    "max_points": max_points_value,
                    "comment": comment_value
                }
        
        mark.task_scores = task_scores
        mark.save()
        
        # Обновляем статус участия
        participation.status = 'graded'
        participation.graded_at = datetime.now()
        participation.save()
        
        messages.success(request, f'Работа {participation.student.get_full_name()} проверена')
        
        # Переход к следующей работе или обратно к событию
        if 'save_and_next' in request.POST:
            # Найти следующую непроверенную работу
            all_participations = list(participation.event.eventparticipation_set.order_by('student__last_name'))
            current_index = all_participations.index(participation)
            
            # Ищем следующую непроверенную работу
            next_participation = None
            for i in range(current_index + 1, len(all_participations)):
                check_participation = all_participations[i]
                if not Mark.objects.filter(participation=check_participation).exists():
                    next_participation = check_participation
                    break
            
            if next_participation:
                return redirect('review:participation-review', pk=next_participation.pk)
            else:
                messages.info(request, 'Все работы в событии проверены!')
                return redirect('review:event-review', pk=participation.event.pk)
        
        return redirect('review:event-review', pk=participation.event.pk)

def ajax_calculate_score(request):
    """AJAX для автоматического расчета оценки по баллам"""
    points = int(request.GET.get('points', 0))
    max_points = int(request.GET.get('max_points', 1))
    
    percentage = (points / max_points) * 100 if max_points > 0 else 0
    
    # Простая шкала перевода в оценку
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
