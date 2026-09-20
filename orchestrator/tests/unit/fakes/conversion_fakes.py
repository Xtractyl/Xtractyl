# orchestrator/tests/unit/fakes/conversion_fakes.py
from db.models import ConversionJob, File, Project
from infrastructure.interfaces.repository import ConversionRepositoryInterface
from infrastructure.interfaces.storage import StorageInterface


class FakeConversionRepo(ConversionRepositoryInterface):
    def __init__(self, existing_projects=None):
        self.projects = {name: Project(name=name) for name in (existing_projects or [])}
        self.files = []
        self.jobs = {}
        self._next_job_id = 1
        self.committed = False
        self.deleted_projects = []

    def project_exists(self, name):
        return name in self.projects

    def create_project(self, name):
        self.projects[name] = Project(name=name)

    def create_file(self, project, filename, pdf_key):
        self.files.append(File(project=project, filename=filename, pdf_key=pdf_key))

    def create_conversion_job(self, project, total_files):
        job_id = self._next_job_id
        self._next_job_id += 1
        self.jobs[job_id] = ConversionJob(
            id=job_id,
            project=project,
            status="pending",
            total_files=total_files,
            converted_files=0,
        )
        return job_id

    def get_conversion_job(self, job_id):
        return self.jobs.get(job_id)

    def get_pdf_keys_for_project(self, project):
        return [f.pdf_key for f in self.files if f.project == project]

    def delete_project_cascade(self, project):
        self.projects.pop(project, None)
        self.files = [f for f in self.files if f.project != project]
        self.jobs = {jid: j for jid, j in self.jobs.items() if j.project != project}
        self.deleted_projects.append(project)

    def set_conversion_job_status(self, job_id, status, error=None):
        job = self.jobs[job_id]
        job.status = status
        if error is not None:
            job.error = error

    def set_file_html_key(self, project, filename, html_key, pdf_hash=None, html_hash=None):
        for f in self.files:
            if f.project == project and f.filename == filename:
                f.html_key = html_key
                f.pdf_hash = pdf_hash
                f.html_hash = html_hash

    def set_file_error(self, project, filename, error):
        for f in self.files:
            if f.project == project and f.filename == filename:
                f.error = error

    def commit(self):
        self.committed = True

    def increment_converted_files(self, job_id):
        self.jobs[job_id].converted_files += 1


class FakeStorage(StorageInterface):
    def __init__(self):
        self.bucket_ensured = False
        self.deleted_prefixes = []

    def ensure_bucket(self):
        self.bucket_ensured = True

    def presigned_put(self, key):
        return f"https://fake-minio/{key}"

    def get_object(self, key):
        raise NotImplementedError("not needed by conversion domain tests yet")

    def delete_prefix(self, prefix):
        self.deleted_prefixes.append(prefix)

    def list_top_level_prefixes(self):
        raise NotImplementedError("not needed by conversion domain tests yet")
