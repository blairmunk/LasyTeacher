"""Payload adapters for sectioned report documents."""


class EventReportDocumentDataProvider:
    CACHE_KEY = 'event_performance_report'

    def __init__(self, get_event_report):
        self.get_event_report = get_event_report

    def get_report(self, request):
        build_context = request.build_context
        if self.CACHE_KEY not in build_context:
            build_context[self.CACHE_KEY] = self.get_event_report(
                request.source.source_id,
            )
        return build_context[self.CACHE_KEY]


class EventReportSectionPayloadBuilder:
    def __init__(self, data_provider):
        self.data_provider = data_provider

    def build_payload(self, request):
        return {
            'report': self.data_provider.get_report(request),
            'options': dict(request.section.options),
        }


class StudentDigestDocumentDataProvider:
    CACHE_KEY = 'student_digest_page'

    def __init__(self, get_student_digests):
        self.get_student_digests = get_student_digests

    def get_page(self, request):
        build_context = request.build_context
        if self.CACHE_KEY not in build_context:
            digest_request = request.section.options.get('digest_request')
            if digest_request is None:
                raise ValueError('Digest request is required.')
            build_context[self.CACHE_KEY] = self.get_student_digests(
                digest_request,
            )
        return build_context[self.CACHE_KEY]

    def get_digest(self, request):
        student_id = request.section.options.get('student_id', '')
        return next(
            (
                digest
                for digest in self.get_page(request).digests
                if digest.student.pk == student_id
            ),
            None,
        )


class StudentDigestSectionPayloadBuilder:
    def __init__(self, data_provider):
        self.data_provider = data_provider

    def build_payload(self, request):
        return {
            'page': self.data_provider.get_page(request),
            'digest': self.data_provider.get_digest(request),
        }
