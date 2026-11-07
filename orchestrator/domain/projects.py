# orchestrator/domain/projects.py
import os

from infrastructure.interfaces.label_studio import LabelStudioInterface
from infrastructure.interfaces.repository import (
    ConversionRepositoryInterface,
    ProjectRepositoryInterface,
)
from infrastructure.interfaces.storage import StorageInterface
from utils.hashing import compute_labels_hash, compute_questions_hash

from domain.errors import (
    InvalidState,
    NotFound,
)
from domain.models.projects import (
    CreateProjectCommand,
    DiscardProjectCommand,
    ProjectExistsCommand,
    ProjectLinksCommand,
    UploadTasksCommand,
)


def check_project_exists(cmd: ProjectExistsCommand, repo: ProjectRepositoryInterface):
    if repo.project_exists(cmd.project):
        raise InvalidState(
            code="PROJECT_ALREADY_EXISTS",
            message="A project with this name already exists.",
        )
    return {"exists": False}


def _ensure_ready_for_creation(title: str, repo: ProjectRepositoryInterface) -> None:
    """Shared by create_project_main_from_payload and get_project_links: both only make
    sense for a project that exists, finished its PDF conversion and has no Label Studio
    project yet."""

    if not repo.project_exists(title):
        raise NotFound(
            code="PROJECT_NOT_FOUND",
            message="No project with this name exists yet. Run PDF conversion for this project first.",
        )

    if not repo.is_conversion_done(
        title
    ):  # necessary check, because we will remove xtractyl project when conversion fails
        raise InvalidState(
            code="CONVERSION_NOT_DONE",
            message="PDF conversion for this project must finish successfully before creating a Label Studio project.",
        )

    if repo.get_label_studio_id(title):
        raise InvalidState(
            code="PROJECT_ALREADY_HAS_LABEL_STUDIO_ID",
            message="A Label Studio project has already been created for this project.",
        )


def create_project_main_from_payload(
    cmd: CreateProjectCommand, repo: ProjectRepositoryInterface, label_studio: LabelStudioInterface
):
    title = cmd.title
    questions = cmd.questions
    labels = cmd.labels
    token = cmd.token

    _ensure_ready_for_creation(title, repo)

    # Label Studio label config
    label_tags = "\n    ".join([f'<Label value="{label}"/>' for label in labels])
    label_config = f"""
    <View>
        <View style="padding: 0.5em 1em; background: #f7f7f7; border-radius: 4px; margin-bottom: 0.5em;">
            <Header value="File: $name" style="font-weight:bold; font-size: 16px; color: #333;" />
        </View>
        <View style="padding: 0 1em; margin: 1em 0; background: #f1f1f1; position: sticky; top: 0; border-radius: 3px; z-index:100">
            <Labels name="label" toName="html">
                {label_tags}
            </Labels>
        </View>
        <HyperText name="html" value="$html" granularity="symbol" />
    </View>"""

    project_id = label_studio.create_project(title, label_config, token)
    label_studio.attach_ml_backend(project_id, token)

    repo.set_label_studio_id(title, project_id)
    repo.save_questions_and_labels(title, {"questions": questions, "labels": labels})

    return {"project_id": project_id}


def list_projects_ready_for_upload(repo: ProjectRepositoryInterface):
    projects = repo.get_projects_ready_for_upload()
    return {"projects": [p.name for p in projects]}


def list_projects_ready_for_creation(repo: ProjectRepositoryInterface):
    projects = repo.get_projects_ready_for_creation()
    return {"projects": [p.name for p in projects]}


def list_projects_ready_for_prelabelling(repo: ProjectRepositoryInterface):
    projects = repo.get_projects_ready_for_prelabelling()
    return {"projects": [p.name for p in projects]}


def upload_tasks_main_from_payload(
    cmd: UploadTasksCommand,
    repo: ProjectRepositoryInterface,
    storage: StorageInterface,
    label_studio: LabelStudioInterface,
):
    label_studio_id = repo.get_label_studio_id(cmd.project)
    if not label_studio_id:
        raise NotFound(
            code="PROJECT_NOT_FOUND",
            message="Project not found or has no Label Studio ID.",
        )
    if repo.tasks_already_uploaded(cmd.project):
        raise InvalidState(
            code="TASKS_ALREADY_UPLOADED",
            message="Tasks have already been uploaded for this project.",
        )
    html_keys = repo.get_html_keys_for_project(cmd.project)
    if not html_keys:
        raise NotFound(
            code="NO_HTML_FILES",
            message="No converted HTML files found for this project.",
        )
    tasks = [
        {"data": {"html": storage.get_object(key), "name": os.path.basename(key)}}
        for key in html_keys
    ]
    label_studio.upload_tasks(label_studio_id, tasks, cmd.token)
    repo.set_ls_tasks_uploaded(cmd.project)
    return {"status": "ok"}


def get_project_links(cmd: ProjectLinksCommand, repo: ProjectRepositoryInterface) -> dict:
    """Backs POST /project-links: tells the user, before the Label Studio project is
    created, which existing projects the new one would be grouped with later. Read-only —
    nothing is stored. Mirrors the matching used by sync_missing_evaluations (comparison)
    and the regression/drift views, but only on labels, questions and documents: model
    and system prompt are not known yet, so regression and drift are only possible if the
    user later chooses the same ones.

    - comparison: same labels and same documents
    - regression: same labels, questions and documents
    - drift: same labels and questions, but no document in common"""
    _ensure_ready_for_creation(cmd.title, repo)

    project = repo.get_project(cmd.title)
    labels_hash = compute_labels_hash(cmd.labels)
    questions_hash = compute_questions_hash(cmd.questions)
    own_html_hashes = repo.get_html_hashes_for_project(cmd.title)

    comparison = repo.list_projects_by_labels_and_documents(labels_hash, project.document_set_hash)
    same_configuration = repo.list_projects_by_labels_and_questions(labels_hash, questions_hash)

    regression = [p for p in same_configuration if p.document_set_hash == project.document_set_hash]
    drift = [
        p
        for p in same_configuration
        if not (repo.get_html_hashes_for_project(p.name) & own_html_hashes)
    ]

    return {
        "comparison": sorted(p.name for p in comparison),
        "regression": sorted(p.name for p in regression),
        "drift": sorted(p.name for p in drift),
    }


def discard_project(
    cmd: DiscardProjectCommand,
    project_repo: ProjectRepositoryInterface,
    conversion_repo: ConversionRepositoryInterface,
    storage: StorageInterface,
) -> dict:
    """Backs POST /discard-project: the user looked at the links shown before creation and
    decided not to continue. Removes a fully converted project that has no Label Studio
    project yet (rows in Postgres, PDFs and HTML in MinIO). discard_conversion cannot do
    this: it refuses jobs that are already 'done'."""
    if not project_repo.project_exists(cmd.project):
        return {"status": "already_gone"}
    if not project_repo.is_conversion_done(cmd.project):
        raise InvalidState(
            code="CONVERSION_NOT_DONE",
            message="Only a project with finished PDF conversion can be discarded here.",
        )
    if project_repo.get_label_studio_id(cmd.project):
        raise InvalidState(
            code="PROJECT_ALREADY_HAS_LABEL_STUDIO_ID",
            message="A Label Studio project exists for this project; it cannot be discarded here.",
        )
    conversion_repo.delete_project_cascade(cmd.project)
    conversion_repo.commit()  # make DB state persistent before making irreversible storage change
    storage.delete_prefix(cmd.project)
    return {"status": "discarded"}
