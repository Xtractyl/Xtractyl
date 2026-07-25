# orchestrator/domain/projects.py
import os

from infrastructure.interfaces.label_studio import LabelStudioInterface
from infrastructure.interfaces.repository import ProjectRepositoryInterface
from infrastructure.interfaces.storage import StorageInterface

from domain.errors import (
    InvalidState,
    NotFound,
)
from domain.models.projects import (
    CreateProjectCommand,
    PreviewQalCommand,
    ProjectExistsCommand,
    UploadTasksCommand,
)


def check_project_exists(cmd: ProjectExistsCommand, repo: ProjectRepositoryInterface):
    if repo.project_exists(cmd.project):
        raise InvalidState(
            code="PROJECT_ALREADY_EXISTS",
            message="A project with this name already exists.",
        )
    return {"exists": False}


def create_project_main_from_payload(
    cmd: CreateProjectCommand, repo: ProjectRepositoryInterface, label_studio: LabelStudioInterface
):
    title = cmd.title
    questions = cmd.questions
    labels = cmd.labels
    token = cmd.token

    if not repo.project_exists(title):
        raise NotFound(
            code="PROJECT_NOT_FOUND",
            message="No project with this name exists yet. Run PDF conversion for this project first.",
        )

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


def preview_qal(cmd: PreviewQalCommand, repo: ProjectRepositoryInterface):
    qal = repo.get_questions_and_labels(cmd.project)
    if not qal:
        raise NotFound(
            code="QAL_NOT_FOUND",
            message="No QAL found for this project.",
        )
    return {"data": qal}


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
