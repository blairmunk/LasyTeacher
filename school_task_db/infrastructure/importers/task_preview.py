"""Read-only task import preview analysis."""

from uuid import UUID

from tasks.models import Task


class TaskImportPreviewAnalyzer:
    def __init__(
        self,
        runtime,
        group_importer,
        topic_importer,
        classification_importer,
    ):
        self.runtime = runtime
        self.group_importer = group_importer
        self.topic_importer = topic_importer
        self.classification_importer = classification_importer

    def analyze(self, json_data):
        tasks_data = json_data.get('tasks', [])
        groups_data = json_data.get('analog_groups', [])
        topics_data = json_data.get('topics', [])
        self.runtime.write(f'  📝 Заданий в файле: {len(tasks_data)}')
        self.runtime.write(f'  📋 Групп аналогов: {len(groups_data)}')
        self.runtime.write(f'  📚 Тем: {len(topics_data)}')

        uuid_counts = self._analyze_uuid_conflicts(json_data)
        dependency_counts = self._analyze_dependencies(json_data)
        return {
            'file_counts': {
                'tasks': len(tasks_data),
                'groups': len(groups_data),
                'topics': len(topics_data),
                'sources': len(json_data.get('sources', [])),
                'images': len(json_data.get('task_images', [])),
            },
            'task_uuid_counts': uuid_counts['tasks'],
            'group_uuid_counts': uuid_counts['groups'],
            'dependency_counts': dependency_counts,
        }

    def _analyze_uuid_conflicts(self, json_data):
        self.runtime.write('\n📊 UUID АНАЛИЗ:')
        task_counts = self._task_uuid_counts(json_data.get('tasks', []))
        group_counts = self._group_uuid_counts(
            json_data.get('analog_groups', []),
        )
        self._write_uuid_counts('📝 ЗАДАНИЯ', task_counts)
        self._write_uuid_counts('📋 ГРУППЫ', group_counts)
        images_count = len(json_data.get('task_images', []))
        if images_count:
            self.runtime.write(f'  🖼️ ИЗОБРАЖЕНИЯ: {images_count}')
        if task_counts['existing'] and self.runtime.mode == 'strict':
            self.runtime.write(
                '  ⚠️ В режиме strict будут ошибки для '
                f"{task_counts['existing']} существующих заданий",
            )
        if task_counts['invalid'] or group_counts['invalid']:
            self.runtime.write('  🚨 Некорректные UUID будут пропущены')
        return {'tasks': task_counts, 'groups': group_counts}

    @staticmethod
    def _task_uuid_counts(tasks_data):
        counts = {'existing': 0, 'new': 0, 'invalid': 0}
        for task_data in tasks_data:
            task_uuid = task_data.get('id')
            try:
                normalized_uuid = UUID(str(task_uuid))
            except (ValueError, TypeError, AttributeError):
                counts['invalid'] += 1
                continue
            key = (
                'existing'
                if Task.objects.filter(pk=normalized_uuid).exists()
                else 'new'
            )
            counts[key] += 1
        return counts

    def _group_uuid_counts(self, groups_data):
        counts = {'existing': 0, 'new': 0, 'invalid': 0}
        for group_data in groups_data:
            group_uuid = group_data.get('id')
            try:
                UUID(str(group_uuid))
            except (ValueError, TypeError, AttributeError):
                counts['invalid'] += 1
                continue
            key = (
                'existing'
                if self.group_importer.find_by_uuid(group_uuid)
                else 'new'
            )
            counts[key] += 1
        return counts

    def _write_uuid_counts(self, label, counts):
        self.runtime.write(f'  {label}:')
        self.runtime.write(f"    🆕 Новых: {counts['new']}")
        self.runtime.write(
            f"    🔄 Существующих: {counts['existing']}",
        )
        self.runtime.write(
            f"    ❌ Некорректных UUID: {counts['invalid']}",
        )

    def _analyze_dependencies(self, json_data):
        self.runtime.write('\n🔍 АНАЛИЗ ЗАВИСИМОСТЕЙ:')
        tasks_data = json_data.get('tasks', [])
        declared_topics = json_data.get('topics', [])
        missing_topics = self._missing_topics(tasks_data, declared_topics)
        missing_subtopics = self._missing_subtopics(
            tasks_data,
            declared_topics,
        )
        missing_groups, broken_references = self._missing_groups(
            tasks_data,
            json_data.get('analog_groups', []),
        )
        missing_classifications = self._missing_classifications(tasks_data)
        self._write_dependencies(
            missing_topics,
            missing_subtopics,
            missing_groups,
            broken_references,
            missing_classifications,
        )
        return {
            'missing_topics': len(missing_topics),
            'missing_subtopics': len(missing_subtopics),
            'missing_groups': len(missing_groups),
            'broken_references': len(broken_references),
            'missing_classifications': len(missing_classifications),
        }

    def _missing_classifications(self, tasks_data):
        missing = []
        for task_data in tasks_data:
            task_id = str(task_data.get('id', ''))[-8:] or '?'
            missing.extend(
                f'Задание {task_id}: {reference}'
                for reference in (
                    self.classification_importer.missing_references(task_data)
                )
            )
        return missing

    def _missing_topics(self, tasks_data, declared_topics):
        declared_ids = {
            str(topic.get('id') or topic.get('uuid') or '')
            for topic in declared_topics
            if isinstance(topic, dict)
        }
        missing = set()
        for task_data in tasks_data:
            topic_data = task_data.get('topic')
            topic_id = self.topic_importer.reference_id(topic_data)
            if (
                not topic_id
                or topic_id in declared_ids
                or self.topic_importer.find(topic_data)
            ):
                continue
            missing.add(topic_id)
        return missing

    def _missing_subtopics(self, tasks_data, declared_topics):
        declared_ids = {
            str(subtopic.get('id') or subtopic.get('uuid') or '')
            for topic in declared_topics
            if isinstance(topic, dict)
            for subtopic in topic.get('subtopics', [])
            if isinstance(subtopic, dict)
        }
        missing = set()
        for task_data in tasks_data:
            subtopic_data = task_data.get('subtopic')
            subtopic_id = self.topic_importer.reference_id(subtopic_data)
            if not subtopic_id or subtopic_id in declared_ids:
                continue
            topic = self.topic_importer.find(task_data.get('topic'))
            if topic and self.topic_importer.resolve_subtopic(
                subtopic_data,
                topic,
            ):
                continue
            missing.add(subtopic_id)
        return missing

    def _missing_groups(self, tasks_data, declared_groups):
        declared_ids = {
            group.get('id')
            for group in declared_groups
            if group.get('id')
        }
        missing = set()
        broken = []
        for task_data in tasks_data:
            task_text = task_data.get('text', 'Unknown')[:30]
            for group_ref in task_data.get('groups', []):
                try:
                    group_uuid, _bank_role = (
                        self.group_importer.parse_reference(group_ref)
                    )
                except ValueError as error:
                    broken.append(f"Задание '{task_text}' → {error}")
                    continue
                if not group_uuid:
                    broken.append(
                        f"Задание '{task_text}' → группа без id",
                    )
                    continue
                if (
                    group_uuid not in declared_ids
                    and not self.group_importer.find_by_uuid(group_uuid)
                ):
                    missing.add(group_uuid)
                    broken.append(
                        f"Задание '{task_text}' → группа {group_uuid[-8:]}",
                    )
        return missing, broken

    def _write_dependencies(
        self,
        missing_topics,
        missing_subtopics,
        missing_groups,
        broken_references,
        missing_classifications,
    ):
        if missing_topics:
            self._write_missing('📚 ОТСУТСТВУЮЩИЕ ТЕМЫ', missing_topics)
            if self.runtime.create_missing:
                self.runtime.write('    ✅ Будут созданы автоматически')
            else:
                self.runtime.write('    ⚠️ Задания без тем будут пропущены')
        if missing_subtopics:
            self._write_missing(
                '📖 ОТСУТСТВУЮЩИЕ ПОДТЕМЫ',
                missing_subtopics,
            )
            self.runtime.write('    ⚠️ Задания останутся без подтем')
        if missing_groups:
            self._write_missing('📋 ОТСУТСТВУЮЩИЕ ГРУППЫ', missing_groups)
            if self.runtime.create_missing:
                self.runtime.write('    ✅ Будут созданы автоматически')
            else:
                self.runtime.write('    ⚠️ Связи будут пропущены')
        if broken_references:
            self._write_missing('🔗 ПРОБЛЕМНЫЕ СВЯЗИ', broken_references)
        if missing_classifications:
            self._write_missing(
                'КЛАССИФИКАЦИИ НЕ НАЙДЕНЫ',
                missing_classifications,
            )

    def _write_missing(self, label, values):
        sorted_values = sorted(values)
        self.runtime.write(f'  {label}: {len(sorted_values)}')
        for value in sorted_values[:3]:
            self.runtime.write(f'    - {value}')
        if len(sorted_values) > 3:
            self.runtime.write(f'    ... и ещё {len(sorted_values) - 3}')
