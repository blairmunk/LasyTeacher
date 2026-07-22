"""Infrastructure helpers for Django review screens."""


class ReviewFormAdapter:
    def dashboard_context(self, dashboard, recent_sessions=None):
        context = {
            'needs_review': dashboard.needs_review,
            'in_progress': dashboard.in_progress,
            'fully_graded': dashboard.fully_graded,
            'total_events': dashboard.total_events,
        }
        if recent_sessions is not None:
            context['recent_sessions'] = recent_sessions
        return context

    def event_review_context(self, review_data, review_session=None):
        context = {
            'event': review_data.event,
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
        }
        if review_session is not None:
            context['review_session'] = review_session
        return context

    def participation_review_context(self, review_data):
        return {
            'participation': review_data.participation,
            'mark': review_data.mark,
            'tasks_with_scores': review_data.tasks_with_scores,
            'typical_comments': review_data.typical_comments,
            'previous_participation': review_data.previous_participation,
            'next_participation': review_data.next_participation,
            'current_position': review_data.current_position,
            'total_positions': review_data.total_positions,
            'navigation_progress': review_data.navigation_progress,
        }

    def score_calculation_payload(self, result):
        return {
            'score': result.score,
            'percentage': result.percentage,
        }
