"""Pure calculations for work analysis reports."""

from collections import Counter

from core_logic.entities.report_summary import (
    WorkAnalysisItem,
    WorkAnalysisReportData,
    WorkAnalysisSource,
    WorkAnalysisSummary,
    WorkScoreDistributionItem,
)


class WorkAnalysisService:
    def build(
        self,
        source: WorkAnalysisSource,
    ) -> WorkAnalysisReportData:
        works_analysis = []
        for item in source.works:
            scores = [
                mark.score
                for mark in item.marks
                if mark.score is not None
            ]
            average_score = (
                round(sum(scores) / len(scores), 2)
                if scores
                else 0
            )
            total_points = sum(mark.points or 0 for mark in item.marks)
            total_max = sum(mark.max_points or 0 for mark in item.marks)
            average_percentage = (
                round(total_points / total_max * 100)
                if total_max > 0
                else 0
            )
            score_counts = Counter(scores)
            score_distribution = tuple(
                WorkScoreDistributionItem(
                    score=score,
                    count=score_counts[score],
                )
                for score in sorted(score_counts)
            )

            works_analysis.append(WorkAnalysisItem(
                work=item.work,
                events=tuple(item.events),
                events_count=item.events_count,
                total_marks=len(item.marks),
                average_score=average_score,
                average_percentage=average_percentage,
                score_distribution=score_distribution,
                difficulty_assessment=self.assess_difficulty(
                    average_percentage,
                ),
            ))

        return WorkAnalysisReportData(
            works_analysis=tuple(works_analysis),
            summary_stats=WorkAnalysisSummary(
                total_works=len(works_analysis),
                total_marks=sum(
                    work.total_marks
                    for work in works_analysis
                ),
                easy_works=sum(
                    1
                    for work in works_analysis
                    if work.difficulty_assessment == 'Легкая'
                ),
                hard_works=sum(
                    1
                    for work in works_analysis
                    if work.difficulty_assessment in (
                        'Сложная',
                        'Очень сложная',
                    )
                ),
                avg_score=(
                    round(
                        sum(
                            work.average_score
                            for work in works_analysis
                        ) / len(works_analysis),
                        2,
                    )
                    if works_analysis
                    else 0
                ),
            ),
            courses=tuple(source.courses),
        )

    @staticmethod
    def assess_difficulty(average_percentage):
        if average_percentage >= 85:
            return 'Легкая'
        if average_percentage >= 70:
            return 'Средняя'
        if average_percentage >= 50:
            return 'Сложная'
        return 'Очень сложная'
