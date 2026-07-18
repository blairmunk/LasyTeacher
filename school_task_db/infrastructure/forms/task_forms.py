"""Infrastructure helpers for Django task forms."""

from core_logic.entities.task import (
    SourceCreateParams,
    TaskImageSaveParams,
    TaskListFilters,
    TaskSaveParams,
)
from tasks.forms import TaskForm, TaskImageFormSet
from tasks.models import Task


class TaskFormAdapter:
    def task_list_filters_from_query(self, query):
        return TaskListFilters(
            search=query.get('search', ''),
            topic_id=query.get('topic', ''),
            subtopic_id=query.get('subtopic', ''),
            task_type=query.get('task_type', ''),
            difficulty=query.get('difficulty', ''),
            group_filter=query.get('group_filter', ''),
            analog_group_id=query.get('analog_group', ''),
            math_filter=query.get('math_filter', 'all'),
            source_id=query.get('source', ''),
            grade=query.get('grade', ''),
            verified=query.get('verified', ''),
        )

    def task_list_filter_context_from_query(self, query):
        return {
            'current_source': query.get('source', ''),
            'current_grade': query.get('grade', ''),
            'current_verified': query.get('verified', ''),
            'current_filter': query.get('math_filter', 'all'),
            'search_query': query.get('search', ''),
            'current_topic': query.get('topic', ''),
            'current_subtopic': query.get('subtopic', ''),
            'current_task_type': query.get('task_type', ''),
            'current_difficulty': query.get('difficulty', ''),
            'current_group_filter': query.get('group_filter', ''),
            'current_analog_group': query.get('analog_group', ''),
        }

    def _get_task_instance(self, task_id=None):
        if not task_id:
            return None
        return Task.objects.filter(pk=task_id).first()

    def build_task_form(self, data=None, task_id=None):
        instance = self._get_task_instance(task_id)
        if data is not None:
            return TaskForm(data, instance=instance)
        return TaskForm(instance=instance)

    def build_image_formset(self, data=None, files=None, instance=None):
        kwargs = {'prefix': 'images'}
        if instance is not None:
            kwargs['instance'] = instance
        if data is not None:
            return TaskImageFormSet(data, files, **kwargs)
        return TaskImageFormSet(**kwargs)

    def build_image_formset_for_task(self, data=None, files=None, task_id=None):
        return self.build_image_formset(
            data=data,
            files=files,
            instance=self._get_task_instance(task_id),
        )

    def task_params_from_form(self, form, task_id=''):
        subtopic = form.cleaned_data.get('subtopic')
        source = form.cleaned_data.get('source')
        return TaskSaveParams(
            task_id=task_id,
            text=form.cleaned_data['text'],
            answer=form.cleaned_data['answer'],
            topic_id=str(form.cleaned_data['topic'].pk),
            subtopic_id=str(subtopic.pk) if subtopic else None,
            task_type=form.cleaned_data['task_type'],
            difficulty=form.cleaned_data['difficulty'],
            cognitive_level=form.cleaned_data.get(
                'cognitive_level',
                'understand',
            ),
            content_element=form.cleaned_data.get('content_element', ''),
            requirement_element=form.cleaned_data.get('requirement_element', ''),
            short_solution=form.cleaned_data.get('short_solution', ''),
            full_solution=form.cleaned_data.get('full_solution', ''),
            hint=form.cleaned_data.get('hint', ''),
            instruction=form.cleaned_data.get('instruction', ''),
            estimated_time=form.cleaned_data.get('estimated_time'),
            source_id=str(source.pk) if source else None,
            source_detail=form.cleaned_data.get('source_detail', ''),
            grade=form.cleaned_data.get('grade'),
            year=form.cleaned_data.get('year'),
            is_verified=form.cleaned_data.get('is_verified', False),
            teacher_notes=form.cleaned_data.get('teacher_notes', ''),
        )

    def task_image_params_from_formset(self, formset):
        images = []
        for row in formset.cleaned_data:
            if not row:
                continue

            image_obj = row.get('id')
            images.append(
                TaskImageSaveParams(
                    image_id=str(image_obj.pk) if image_obj else '',
                    image=row.get('image'),
                    position=row.get('position', ''),
                    caption=row.get('caption', ''),
                    order=row.get('order') or 1,
                    delete=row.get('DELETE', False),
                )
            )
        return images

    def source_params_from_form(self, form):
        return SourceCreateParams(
            name=form.cleaned_data['name'],
            short_name=form.cleaned_data.get('short_name', ''),
            source_type=form.cleaned_data.get('source_type', 'textbook'),
            author=form.cleaned_data.get('author', ''),
            year=form.cleaned_data.get('year'),
            url=form.cleaned_data.get('url', ''),
            isbn=form.cleaned_data.get('isbn', ''),
            notes=form.cleaned_data.get('notes', ''),
        )
