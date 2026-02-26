# reports/views.py

import json
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta

from . import plotly_utils


class ReportsDashboardView(TemplateView):
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = datetime.now()
        
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
            'average_score': marks.aggregate(
                avg_score=Avg('score')
            )['avg_score'] or 0,
            'marks_last_month': marks.filter(
                checked_at__gte=current_date - timedelta(days=30)
            ).count(),
        })
        
        # Распределение оценок — Plotly
        score_counts = {}
        for item in marks.exclude(score__isnull=True).values('score').annotate(
            count=Count('score')
        ):
            score_counts[item['score']] = item['count']
        
        context['score_distribution'] = list(
            marks.exclude(score__isnull=True).values('score').annotate(
                count=Count('score')
            ).order_by('score')
        )
        context['score_chart_json'] = plotly_utils.to_json(
            plotly_utils.score_distribution_config(score_counts)
        )
        
        # Статистика по событиям
        context.update({
            'events_planned': Event.objects.filter(status='planned').count(),
            'events_completed': Event.objects.filter(status='completed').count(),
            'events_graded': Event.objects.filter(status='graded').count(),
        })
        
        # Активность по месяцам — Plotly
        monthly_labels = []
        monthly_values = []
        for i in range(6):
            month_start = current_date.replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=31)
            count = EventParticipation.objects.filter(
                event__planned_date__range=[month_start, month_end],
                status__in=['completed', 'graded']
            ).count()
            monthly_labels.append(month_start.strftime('%b %Y'))
            monthly_values.append(count)
        
        monthly_labels.reverse()
        monthly_values.reverse()
        context['activity_chart_json'] = plotly_utils.to_json(
            plotly_utils.line_chart_config(
                monthly_labels, monthly_values,
                title='Активность по месяцам'
            )
        )
        
        # Статистика по классам — Plotly
        class_stats = []
        class_names = []
        class_avg_scores = []
        class_completion = []
        
        for student_group in StudentGroup.objects.all():
            students_ids = list(
                student_group.students.values_list('id', flat=True)
            )
            participations = EventParticipation.objects.filter(
                student__id__in=students_ids
            )
            completed = participations.filter(
                status__in=['completed', 'graded']
            )
            class_marks = Mark.objects.filter(
                participation__student__id__in=students_ids,
                score__isnull=False
            )
            avg_score = class_marks.aggregate(avg=Avg('score'))['avg'] or 0
            completion_rate = round(
                (completed.count() / participations.count() * 100)
                if participations.count() > 0 else 0, 1
            )
            
            # Ссылки на heatmap — только для привязанных курсов
            heatmap_links = []
            linked_courses = student_group.courses.all()
            for c in linked_courses:
                heatmap_links.append({
                    'course_id': str(c.pk),
                    'course_name': c.name,
                    'group_id': str(student_group.pk),
                    'group_name': student_group.name,
                })
            
            stat = {
                'name': student_group.name,
                'students_count': student_group.students.count(),
                'total_participations': participations.count(),
                'completed_participations': completed.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': completion_rate,
                'id': str(student_group.id),
                'heatmap_links': heatmap_links,
            }
            class_stats.append(stat)
            class_names.append(student_group.name)
            class_avg_scores.append(round(avg_score, 2))
            class_completion.append(completion_rate)
        
        context['class_stats'] = class_stats

        context['class_chart_json'] = plotly_utils.to_json(
            plotly_utils.multi_bar_config(
                class_names,
                {
                    'Средний балл': class_avg_scores,
                    '% выполнения (÷25)': [
                        round(c / 25, 2) for c in class_completion
                    ],
                },
                title='Сравнение классов'
            )
        )
        
        # Топ учеников
        top_students = Student.objects.annotate(
            completed_works=Count(
                'eventparticipation',
                filter=Q(
                    eventparticipation__status__in=['completed', 'graded']
                )
            )
        ).order_by('-completed_works')[:10]
        context['top_students'] = top_students
        
        # Последние события
        recent_events = Event.objects.select_related(
            'work', 'course'
        ).order_by('-planned_date')[:10]
        context['recent_events'] = recent_events
        
        # События требующие внимания
        events_need_attention = Event.objects.filter(
            Q(status='reviewing') |
            Q(status='completed',
              planned_date__lt=current_date - timedelta(days=7))
        ).select_related('work')[:5]
        context['events_need_attention'] = events_need_attention
        
        # Типы работ
        work_type_stats = Work.objects.values('work_type').annotate(
            count=Count('id'), avg_duration=Avg('duration')
        ).order_by('-count')
        context['work_type_stats'] = list(work_type_stats)
        
        # Доступные курсы и классы для heatmap
        context['courses'] = Course.objects.all()
        context['student_groups'] = StudentGroup.objects.all()
        
        return context


class HeatmapView(TemplateView):
    """Тепловая карта успеваемости"""
    template_name = 'reports/heatmap.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from students.models import StudentGroup
        from curriculum.models import Course
        
        # Параметры из GET
        course_id = self.request.GET.get('course', '')
        group_id = self.request.GET.get('group', '')
        
        # Все курсы — всегда показываем
        all_courses = Course.objects.all()
        context['courses'] = all_courses
        context['selected_course'] = course_id
        context['selected_group'] = group_id
        
        # Группы: если курс выбран — только привязанные, иначе все
        selected_course_obj = None
        if course_id:
            try:
                selected_course_obj = Course.objects.get(pk=course_id)
                linked_groups = selected_course_obj.student_groups.all()
                if linked_groups.exists():
                    context['student_groups'] = linked_groups
                else:
                    context['student_groups'] = StudentGroup.objects.all()
            except (Course.DoesNotExist, ValueError):
                context['student_groups'] = StudentGroup.objects.all()
        else:
            context['student_groups'] = StudentGroup.objects.all()
        
        # Если оба параметра выбраны — строим карту
        if course_id and group_id:
            try:
                course = selected_course_obj or Course.objects.get(pk=course_id)
                group = StudentGroup.objects.get(pk=group_id)
                context['course'] = course
                context['group'] = group
                
                heatmap_data = self._build_heatmap(course, group)
                context['heatmap_data'] = heatmap_data
                
                if heatmap_data['students'] and heatmap_data['groups']:
                    chart = plotly_utils.heatmap_config(
                        students=heatmap_data['students'],
                        groups=heatmap_data['groups'],
                        matrix=heatmap_data['matrix'],
                        title=f'Успеваемость: {group.name} — {course.name}',
                    )
                    context['heatmap_json'] = plotly_utils.to_json(chart)
                    context['stats'] = self._calc_stats(heatmap_data)
                else:
                    context['error'] = 'Нет данных для построения карты'
                
            except (Course.DoesNotExist, StudentGroup.DoesNotExist, ValueError) as e:
                context['error'] = f'Курс или класс не найден: {e}'
        
        return context
    
    def _build_heatmap(self, course, group):
        """Построение матрицы оценок: студенты × группы аналогов"""
        from events.models import Event, Mark
        from works.models import WorkAnalogGroup
        from curriculum.models import CourseAssignment
        
        # Ученики класса
        students = list(
            group.students.all().order_by('last_name', 'first_name')
        )
        
        # Работы курса
        course_work_ids = list(
            CourseAssignment.objects.filter(
                course=course
            ).values_list('work_id', flat=True)
        )
        
        # Группы аналогов из работ курса
        work_ag_links = WorkAnalogGroup.objects.filter(
            work_id__in=course_work_ids
        ).select_related('analog_group').order_by('analog_group__name')
        
        ag_dict = {}
        ag_to_works = {}
        for wag in work_ag_links:
            ag = wag.analog_group
            if ag.id not in ag_dict:
                ag_dict[ag.id] = ag
                ag_to_works[ag.id] = set()
            ag_to_works[ag.id].add(wag.work_id)
        
        analog_groups = list(ag_dict.values())
        
        # События курса
        events = Event.objects.filter(
            work_id__in=course_work_ids,
            course=course,
        )
        
        # Все оценки
        student_ids = [s.id for s in students]
        marks = Mark.objects.filter(
            participation__event__in=events,
            participation__student_id__in=student_ids,
            score__isnull=False,
        ).select_related('participation', 'participation__event')
        
        sw_scores = {}
        for mark in marks:
            key = (
                mark.participation.student_id,
                mark.participation.event.work_id
            )
            if key not in sw_scores:
                sw_scores[key] = []
            sw_scores[key].append(mark.score)
        
        # Матрица
        matrix = []
        for student in students:
            row = []
            for ag in analog_groups:
                work_ids = ag_to_works.get(ag.id, set())
                scores = []
                for work_id in work_ids:
                    key = (student.id, work_id)
                    if key in sw_scores:
                        scores.extend(sw_scores[key])
                
                if scores:
                    row.append(round(sum(scores) / len(scores), 2))
                else:
                    row.append(None)
            matrix.append(row)
        
        short_names = [
            f'{s.last_name} {s.first_name[0]}.' for s in students
        ]
        group_names = [ag.name for ag in analog_groups]
        
        return {
            'students': short_names,
            'student_objects': students,
            'groups': group_names,
            'group_objects': analog_groups,
            'matrix': matrix,
        }
    
    def _calc_stats(self, heatmap_data):
        """Статистика по тепловой карте"""
        matrix = heatmap_data['matrix']
        students = heatmap_data['students']
        groups = heatmap_data['groups']
        
        student_avgs = []
        for i, row in enumerate(matrix):
            vals = [v for v in row if v is not None]
            avg = sum(vals) / len(vals) if vals else None
            student_avgs.append({
                'name': students[i],
                'avg': round(avg, 2) if avg else None,
                'count': len(vals),
            })
        
        group_avgs = []
        for j, gname in enumerate(groups):
            vals = [
                matrix[i][j] for i in range(len(students))
                if matrix[i][j] is not None
            ]
            avg = sum(vals) / len(vals) if vals else None
            group_avgs.append({
                'name': gname,
                'avg': round(avg, 2) if avg else None,
                'count': len(vals),
            })
        
        problem_zones = []
        excellent_zones = []
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                if val is not None and val < 3:
                    problem_zones.append({
                        'student': students[i],
                        'group': groups[j],
                        'score': val,
                    })
                if val is not None and val >= 4.5:
                    excellent_zones.append({
                        'student': students[i],
                        'group': groups[j],
                        'score': val,
                    })
        
        student_avgs.sort(key=lambda x: x['avg'] or 0, reverse=True)
        group_avgs.sort(key=lambda x: x['avg'] or 0)
        
        all_vals = [v for row in matrix for v in row if v is not None]
        overall_avg = round(
            sum(all_vals) / len(all_vals), 2
        ) if all_vals else 0
        
        return {
            'student_avgs': student_avgs,
            'group_avgs': group_avgs,
            'problem_zones': problem_zones[:10],
            'excellent_zones': excellent_zones[:10],
            'overall_avg': overall_avg,
            'total_cells': len(students) * len(groups),
            'filled_cells': len(all_vals),
            'empty_cells': len(students) * len(groups) - len(all_vals),
        }

class StudentPerformanceView(TemplateView):
    """Отчет по успеваемости учеников"""
    template_name = 'reports/student_performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from students.models import Student
        from events.models import Mark, EventParticipation
        
        students_stats = []
        high_performers_count = 0
        students_with_scores = 0
        students_with_activity = 0
        total_completion_rate = 0
        total_average_score = 0
        
        for student in Student.objects.all():
            participations = student.eventparticipation_set.all()
            completed = participations.filter(
                status__in=['completed', 'graded']
            )
            student_marks = Mark.objects.filter(
                participation__student=student, score__isnull=False
            )
            avg_score = student_marks.aggregate(
                avg=Avg('score')
            )['avg'] or 0
            completion_rate = round(
                (completed.count() / participations.count() * 100)
                if participations.count() > 0 else 0, 1
            )
            
            students_stats.append({
                'student': student,
                'total_participations': participations.count(),
                'completed_participations': completed.count(),
                'total_marks': student_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': completion_rate,
                'last_activity': participations.order_by(
                    '-created_at'
                ).first()
            })
            
            if participations.count() > 0:
                total_completion_rate += completion_rate
                students_with_activity += 1
            if avg_score > 0:
                total_average_score += avg_score
                students_with_scores += 1
                if avg_score >= 4.5:
                    high_performers_count += 1
        
        students_stats.sort(
            key=lambda x: x['average_score'], reverse=True
        )
        
        context['students_stats'] = students_stats
        context['summary_stats'] = {
            'total_students': len(students_stats),
            'high_performers': high_performers_count,
            'avg_completion_rate': round(
                total_completion_rate / students_with_activity, 1
            ) if students_with_activity > 0 else 0,
            'avg_score': round(
                total_average_score / students_with_scores, 1
            ) if students_with_scores > 0 else 0,
        }
        
        return context


class WorkAnalysisView(TemplateView):
    """Анализ работ и их результатов"""
    template_name = 'reports/work_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from works.models import Work
        from events.models import Event, Mark
        
        works_analysis = []
        easy_works_count = 0
        hard_works_count = 0
        total_marks_all = 0
        
        for work in Work.objects.all():
            work_events = Event.objects.filter(work=work)
            work_marks = Mark.objects.filter(
                participation__event__work=work, score__isnull=False
            )
            avg_score = work_marks.aggregate(
                avg=Avg('score')
            )['avg'] or 0
            avg_percentage = work_marks.aggregate(
                avg=Avg('points')
            )['avg'] or 0
            score_dist = work_marks.values('score').annotate(
                count=Count('score')
            ).order_by('score')
            difficulty = self.assess_difficulty(avg_score, avg_percentage)
            
            works_analysis.append({
                'work': work,
                'events_count': work_events.count(),
                'total_marks': work_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'average_percentage': round(
                    avg_percentage, 1
                ) if avg_percentage else 0,
                'score_distribution': list(score_dist),
                'difficulty_assessment': difficulty,
            })
            
            if difficulty == "Лёгкая":
                easy_works_count += 1
            elif difficulty in ["Сложная", "Очень сложная"]:
                hard_works_count += 1
            total_marks_all += work_marks.count()
        
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
        if avg_score >= 4.5:
            return "Лёгкая"
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
        
        events_by_status = Event.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        context['events_by_status'] = list(events_by_status)
        
        current_date = datetime.now()
        
        context.update({
            'overdue_events': Event.objects.filter(
                status='planned',
                planned_date__lt=current_date - timedelta(days=1)
            ).select_related('work'),
            'long_reviewing': Event.objects.filter(
                status='reviewing',
                actual_end__lt=current_date - timedelta(days=7)
            ).select_related('work'),
            'completed_unchecked': Event.objects.filter(
                status='completed',
                actual_end__lt=current_date - timedelta(days=3)
            ).select_related('work'),
        })
        
        participation_stats = EventParticipation.objects.values(
            'status'
        ).annotate(count=Count('id')).order_by('status')
        context['participation_stats'] = list(participation_stats)
        
        return context
