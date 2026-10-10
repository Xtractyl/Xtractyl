# orchestrator/tests/unit/fakes/project_repository.py
from infrastructure.interfaces.repository import ProjectRepositoryInterface


class FakeProjectRepo(ProjectRepositoryInterface):
    def __init__(
        self,
        label_studio_ids=None,
        questions_and_labels=None,
        tasks_uploaded=(),
        html_keys=None,
    ):
        self.document_set_hashes_set = []
        self._label_studio_ids = label_studio_ids or {}
        self._questions_and_labels = questions_and_labels or {}
        self._tasks_uploaded = set(tasks_uploaded)
        self._html_keys = html_keys or {}

    def set_document_set_hash(self, name):
        self.document_set_hashes_set.append(name)

    def get_label_studio_id(self, name):
        return self._label_studio_ids.get(name)

    def get_questions_and_labels(self, name):
        return self._questions_and_labels.get(name)

    def tasks_already_uploaded(self, name):
        return name in self._tasks_uploaded

    def get_html_keys_for_project(self, name):
        return self._html_keys.get(name, [])

    def project_exists(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def get_project(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def set_label_studio_id(self, name, label_studio_id):
        raise NotImplementedError("not needed by domain tests yet")

    def get_projects_ready_for_upload(self):
        raise NotImplementedError("not needed by domain tests yet")

    def get_projects_ready_for_creation(self):
        raise NotImplementedError("not needed by domain tests yet")

    def get_projects_ready_for_prelabelling(self):
        raise NotImplementedError("not needed by domain tests yet")

    def is_conversion_done(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def set_ls_tasks_uploaded(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def save_questions_and_labels(self, name, qal):
        raise NotImplementedError("not needed by domain tests yet")

    def get_groundtruth_scope(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def get_projects_ready_for_groundtruth(self):
        raise NotImplementedError("not needed by domain tests yet")

    def set_groundtruth(self, name, scope):
        raise NotImplementedError("not needed by domain tests yet")

    def list_groundtruth_projects(self):
        raise NotImplementedError("not needed by domain tests yet")

    def get_html_hashes_for_project(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def get_groundtruth_annotations(self, project):
        raise NotImplementedError("not needed by domain tests yet")

    def is_groundtruth(self, name):
        raise NotImplementedError("not needed by domain tests yet")

    def save_groundtruth_annotations(self, project, annotations):
        raise NotImplementedError("not needed by domain tests yet")
