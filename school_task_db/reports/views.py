from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta

class ReportsDashboardView(TemplateView):
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = datetime.now()
        
        # Импорты внутри метода для избежания циклических импортов
        from students.models import Student, StudentGroup
        from events.models import Event, EventParticipation, Mark
        from works.models import Work
        from curriculum.models import Course
        
        # Основная статистика
        context.update({
            'total_students': Student.objects.count(),
            'total_events': Event.objects.count(),
            'total_works': Work.objects.count(),
            'total_courses': Course.objects.count(),
        })
        
        # Статистика по отметкам
        marks = Mark.objects.all()
        context.update({
            'total_marks': marks.count(),
            'average_score': marks.aggregate(avg_score=Avg('score'))['avg_score'] or 0,
            'marks_last_month': marks.filter(
                checked_at__gte=current_date - timedelta(days=30)
            ).count(),
        })
        
        # Распределение оценок
        score_distribution = marks.exclude(score__isnull=True).values('score').annotate(
            count=Count('score')
        ).order_by('score')
        context['score_distribution'] = list(score_distribution)
        
        # Статистика по событиям
        context.update({
            'events_planned': Event.objects.filter(status='planned').count(),
            'events_completed': Event.objects.filter(status='completed').count(),
            'events_graded': Event.objects.filter(status='graded').count(),
        })
        
        # Активность по месяцам
        monthly_activity = []
        for i in range(6):
            month_start = current_date.replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=31)
            
            participations_count = EventParticipation.objects.filter(
                event__planned_date__range=[month_start, month_end],
                status__in=['completed', 'graded']
            ).count()
            
            monthly_activity.append({
                'month': month_start.strftime('%Y-%m'),
                'participations': participations_count
            })
        
        context['monthly_activity'] = list(reversed(monthly_activity))
        
        # Топ активных учеников
        top_students = Student.objects.annotate(
            completed_works=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status__in=['completed', 'graded'])
            )
        ).order_by('-completed_works')[:10]
        context['top_students'] = top_students
        
        # Статистика по классам
        class_stats = []
        for student_group in StudentGroup.objects.all():
            students_ids = list(student_group.students.values_list('id', flat=True))
            
            participations = EventParticipation.objects.filter(
                student__id__in=students_ids
            )
            
            completed_participations = participations.filter(
                status__in=['completed', 'graded']
            )
            
            class_marks = Mark.objects.filter(
                participation__student__id__in=students_ids,
                score__isnull=False
            )
            avg_score = class_marks.aggregate(avg=Avg('score'))['avg'] or 0
            
            class_stats.append({
                'name': student_group.name,
                'students_count': student_group.students.count(),
                'total_participations': participations.count(),
                'completed_participations': completed_participations.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': round(
                    (completed_participations.count() / participations.count() * 100) 
                    if participations.count() > 0 else 0, 1
                )
            })
        
        context['class_stats'] = class_stats
        
        # Последние события
        recent_events = Event.objects.select_related('work', 'course').order_by('-planned_date')[:10]
        context['recent_events'] = recent_events
        
        # События требующие внимания
        events_need_attention = Event.objects.filter(
            Q(status='reviewing') | 
            Q(status='completed', planned_date__lt=current_date - timedelta(days=7))
        ).select_related('work')[:5]
        context['events_need_attention'] = events_need_attention
        
        # Статистика по типам работ
        work_type_stats = Work.objects.values('work_type').annotate(
            count=Count('id'),
            avg_duration=Avg('duration')
        ).order_by('-count')
        context['work_type_stats'] = list(work_type_stats)
        
        return context

class StudentPerformanceView(TemplateView):
    """Отчет по успеваемости учеников"""
    template_name = 'reports/student_performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from students.models import Student
        from events.models import Mark, EventParticipation
        
        # Получаем статистику по каждому ученику
        students_stats = []
        total_completion_rate = 0
        total_average_score = 0
        high_performers_count = 0
        students_with_scores = 0
        students_with_activity = 0
        
        for student in Student.objects.all():
            # Участие в событиях
            participations = student.eventparticipation_set.all()
            completed_participations = participations.filter(status__in=['completed', 'graded'])
            
            # Отметки ученика
            student_marks = Mark.objects.filter(participation__student=student, score__isnull=False)
            
            avg_score = student_marks.aggregate(avg=Avg('score'))['avg'] or 0
            completion_rate = round(
                (completed_participations.count() / participations.count() * 100) 
                if participations.count() > 0 else 0, 1
            )
            
            students_stats.append({
                'student': student,
                'total_participations': participations.count(),
                'completed_participations': completed_participations.count(),
                'total_marks': student_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': completion_rate,
                'last_activity': participations.order_by('-created_at').first()
            })
            
            # Вычисляем общую статистику
            if participations.count() > 0:
                total_completion_rate += completion_rate
                students_with_activity += 1
            
            if avg_score > 0:
                total_average_score += avg_score
                students_with_scores += 1
                
                if avg_score >= 4.5:
                    high_performers_count += 1
        
        # Сортируем по средней оценке
        students_stats.sort(key=lambda x: x['average_score'], reverse=True)
        
        # Вычисляем общую статистику
        context['students_stats'] = students_stats
        context['summary_stats'] = {
            'total_students': len(students_stats),
            'high_performers': high_performers_count,
            'avg_completion_rate': round(total_completion_rate / students_with_activity, 1) if students_with_activity > 0 else 0,
            'avg_score': round(total_average_score / students_with_scores, 1) if students_with_scores > 0 else 0,
        }
        
        return context

class WorkAnalysisView(TemplateView):
    """Анализ работ и их результатов"""
    template_name = 'reports/work_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from works.models import Work
        from events.models import Event, Mark
        
        # Анализ каждой работы
        works_analysis = []
        easy_works_count = 0
        hard_works_count = 0
        total_marks_all = 0
        
        for work in Work.objects.all():
            # События по этой работе
            work_events = Event.objects.filter(work=work)
            
            # Все отметки по этой работе
            work_marks = Mark.objects.filter(
                participation__event__work=work,
                score__isnull=False
            )
            
            # Статистика
            avg_score = work_marks.aggregate(avg=Avg('score'))['avg'] or 0
            avg_percentage = work_marks.aggregate(avg=Avg('points'))['avg'] or 0
            
            # Распределение оценок
            score_dist = work_marks.values('score').annotate(count=Count('score')).order_by('score')
            
            # Оценка сложности
            difficulty = self.assess_difficulty(avg_score, avg_percentage)
            
            work_analysis = {
                'work': work,
                'events_count': work_events.count(),
                'total_marks': work_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'average_percentage': round(avg_percentage, 1) if avg_percentage else 0,
                'score_distribution': list(score_dist),
                'difficulty_assessment': difficulty
            }
            
            works_analysis.append(work_analysis)
            
            # Подсчет для общей статистики
            if difficulty == "Легкая":
                easy_works_count += 1
            elif difficulty in ["Сложная", "Очень сложная"]:
                hard_works_count += 1
            
            total_marks_all += work_marks.count()
        
        # Сортируем по сложности (низкие оценки = сложные работы)
        works_analysis.sort(key=lambda x: x['average_score'])
        
        context['works_analysis'] = works_analysis
        context['summary_stats'] = {
            'total_works': len(works_analysis),
            'easy_works': easy_works_count,
            'hard_works': hard_works_count,
            'total_marks': total_marks_all,
        }
        
        return context
    
    def assess_difficulty(self, avg_score, avg_percentage):
        """Оценка сложности работы"""
        if avg_score >= 4.5:
            return "Легкая"
        elif avg_score >= 3.5:
            return "Средняя"
        elif avg_score >= 2.5:
            return "Сложная"
        else:
            return "Очень сложная"

class EventsStatusView(TemplateView):
    """Отчет по статусам событий"""
    template_name = 'reports/events_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from events.models import Event, EventParticipation
        from datetime import datetime, timedelta
        
        # События по статусам
        events_by_status = Event.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        context['events_by_status'] = list(events_by_status)
        
        # События требующие действий
        current_date = datetime.now()
        
        # Просроченные запланированные события
        overdue_events = Event.objects.filter(
            status='planned',
            planned_date__lt=current_date - timedelta(days=1)
        ).select_related('work')
        
        # События на проверке более недели
        long_reviewing = Event.objects.filter(
            status='reviewing',
            actual_end__lt=current_date - timedelta(days=7)
        ).select_related('work')
        
        # Завершенные события без проверки
        completed_unchecked = Event.objects.filter(
            status='completed',
            actual_end__lt=current_date - timedelta(days=3)
        ).select_related('work')
        
        context.update({
            'overdue_events': overdue_events,
            'long_reviewing': long_reviewing,
            'completed_unchecked': completed_unchecked,
        })
        
        # Детальная статистика по участию
        participation_stats = EventParticipation.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        context['participation_stats'] = list(participation_stats)
        
        return context
