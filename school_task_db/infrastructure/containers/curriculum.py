"""Curriculum and codifier wiring for the dependency container."""

from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase
from core_logic.use_cases.get_course_list import GetCourseListUseCase
from core_logic.use_cases.get_topic_detail import GetTopicDetailUseCase
from core_logic.use_cases.get_topic_list import GetTopicListUseCase
from core_logic.use_cases.get_topic_subtopics import GetTopicSubtopicsUseCase
from core_logic.use_cases.import_codifier import ImportCodifierUseCase
from core_logic.use_cases.import_curriculum import ImportCurriculumUseCase
from infrastructure.forms.codifier_forms import CodifierFormAdapter
from infrastructure.forms.curriculum_forms import CurriculumFormAdapter
from infrastructure.repositories.django_codifier_catalog_repo import (
    DjangoCodifierCatalogRepository,
)
from infrastructure.repositories.django_codifier_detail_repo import (
    DjangoCodifierDetailRepository,
)
from infrastructure.repositories.django_codifier_import_repo import (
    DjangoCodifierImportRepository,
)
from infrastructure.repositories.django_course_catalog_repo import (
    DjangoCourseCatalogRepository,
)
from infrastructure.repositories.django_curriculum_import_repo import (
    DjangoCurriculumImportRepository,
)
from infrastructure.repositories.django_topic_catalog_repo import (
    DjangoTopicCatalogRepository,
)


class CurriculumCompositionMixin:
    """Owns curriculum, topic, and codifier infrastructure wiring."""

    def _initialize_curriculum_composition(self):
        self._course_catalog_repo = None
        self._topic_catalog_repo = None
        self._curriculum_import_repo = None
        self._codifier_catalog_repo = None
        self._codifier_detail_repo = None
        self._codifier_import_repo = None
        self._codifier_form_adapter = None
        self._curriculum_form_adapter = None

    @property
    def course_catalog_repo(self):
        if self._course_catalog_repo is None:
            self._course_catalog_repo = DjangoCourseCatalogRepository()
        return self._course_catalog_repo

    @property
    def topic_catalog_repo(self):
        if self._topic_catalog_repo is None:
            self._topic_catalog_repo = DjangoTopicCatalogRepository()
        return self._topic_catalog_repo

    @property
    def codifier_catalog_repo(self):
        if self._codifier_catalog_repo is None:
            self._codifier_catalog_repo = DjangoCodifierCatalogRepository()
        return self._codifier_catalog_repo

    @property
    def codifier_detail_repo(self):
        if self._codifier_detail_repo is None:
            self._codifier_detail_repo = DjangoCodifierDetailRepository()
        return self._codifier_detail_repo

    @property
    def codifier_import_repo(self):
        if self._codifier_import_repo is None:
            self._codifier_import_repo = DjangoCodifierImportRepository()
        return self._codifier_import_repo

    @property
    def curriculum_import_repo(self):
        if self._curriculum_import_repo is None:
            self._curriculum_import_repo = DjangoCurriculumImportRepository()
        return self._curriculum_import_repo

    @property
    def codifier_form_adapter(self):
        if self._codifier_form_adapter is None:
            self._codifier_form_adapter = CodifierFormAdapter()
        return self._codifier_form_adapter

    @property
    def curriculum_form_adapter(self):
        if self._curriculum_form_adapter is None:
            self._curriculum_form_adapter = CurriculumFormAdapter()
        return self._curriculum_form_adapter

    def import_codifier_use_case(self):
        return ImportCodifierUseCase(
            codifier_repo=self.codifier_import_repo,
            transaction_manager=self.transaction_manager,
        )

    def import_curriculum_use_case(self):
        return ImportCurriculumUseCase(
            curriculum_repo=self.curriculum_import_repo,
            transaction_manager=self.transaction_manager,
        )

    def get_course_detail_use_case(self):
        return GetCourseDetailUseCase(
            curriculum_repo=self.course_catalog_repo,
        )

    def get_course_list_use_case(self):
        return GetCourseListUseCase(
            curriculum_repo=self.course_catalog_repo,
        )

    def get_topic_subtopics_use_case(self):
        return GetTopicSubtopicsUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_topic_list_use_case(self):
        return GetTopicListUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_topic_detail_use_case(self):
        return GetTopicDetailUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_codifier_list_use_case(self):
        return GetCodifierListUseCase(
            codifier_repo=self.codifier_catalog_repo,
        )

    def get_codifier_detail_use_case(self):
        return GetCodifierDetailUseCase(
            codifier_repo=self.codifier_detail_repo,
        )
