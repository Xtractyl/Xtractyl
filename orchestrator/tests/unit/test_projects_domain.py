# orchestrator/tests/unit/test_projects_domain.py
import pytest
from db.models import Project
from domain.errors import InvalidState, NotFound
from domain.models.projects import DiscardProjectCommand, ProjectLinksCommand
from domain.projects import discard_project, get_project_links
from utils.hashing import compute_document_set_hash, compute_labels_hash, compute_questions_hash

from tests.unit.fakes.conversion_repository import FakeConversionRepo
from tests.unit.fakes.project_repository import FakeProjectRepo
from tests.unit.fakes.storage import FakeStorage

LABELS = ["Date", "Name"]
QUESTIONS = ["When?", "Who?"]
DOCS = {"h1", "h2"}


def make_other(name, labels=LABELS, questions=QUESTIONS, docs=DOCS):
    """An already created project: it has labels/questions hashes, the new one has none yet."""
    project = Project(
        name=name,
        labels_hash=compute_labels_hash(labels),
        questions_hash=compute_questions_hash(questions),
        document_set_hash=compute_document_set_hash(docs),
    )
    return project, docs


def make_repo(others=(), new_docs=DOCS, conversion_done=("new",), label_studio_ids=None):
    """Repo containing the converted project "new" plus the given other projects."""
    new = Project(name="new", document_set_hash=compute_document_set_hash(new_docs))
    html_hashes = {"new": set(new_docs)}
    html_hashes.update({project.name: set(docs) for project, docs in others})
    return FakeProjectRepo(
        projects=[new] + [project for project, _ in others],
        conversion_done=conversion_done,
        html_hashes=html_hashes,
        label_studio_ids=label_studio_ids,
    )


def links_cmd(labels=LABELS, questions=QUESTIONS):
    return ProjectLinksCommand(title="new", questions=questions, labels=labels)


# --- get_project_links ---


def test_get_project_links_rejects_unknown_project():
    with pytest.raises(NotFound) as exc:
        get_project_links(links_cmd(), repo=FakeProjectRepo())

    assert exc.value.code == "PROJECT_NOT_FOUND"


def test_get_project_links_rejects_project_without_finished_conversion():
    repo = make_repo(conversion_done=())

    with pytest.raises(InvalidState) as exc:
        get_project_links(links_cmd(), repo=repo)

    assert exc.value.code == "CONVERSION_NOT_DONE"


def test_get_project_links_rejects_project_with_label_studio_project():
    repo = make_repo(label_studio_ids={"new": 5})

    with pytest.raises(InvalidState) as exc:
        get_project_links(links_cmd(), repo=repo)

    assert exc.value.code == "PROJECT_ALREADY_HAS_LABEL_STUDIO_ID"


def test_get_project_links_returns_empty_lists_without_matches():
    result = get_project_links(links_cmd(), repo=make_repo())

    assert result == {"comparison": [], "regression": [], "drift": []}


def test_same_labels_and_documents_is_comparison_only_when_questions_differ():
    repo = make_repo(others=[make_other("other", questions=["Other question?", "Who?"])])

    result = get_project_links(links_cmd(), repo=repo)

    assert result == {"comparison": ["other"], "regression": [], "drift": []}


def test_same_labels_questions_and_documents_is_comparison_and_regression():
    repo = make_repo(others=[make_other("other")])

    result = get_project_links(links_cmd(), repo=repo)

    assert result == {"comparison": ["other"], "regression": ["other"], "drift": []}


def test_same_labels_and_questions_with_disjoint_documents_is_drift_only():
    repo = make_repo(others=[make_other("other", docs={"h3", "h4"})])

    result = get_project_links(links_cmd(), repo=repo)

    assert result == {"comparison": [], "regression": [], "drift": ["other"]}


def test_partly_overlapping_documents_are_no_match_at_all():
    repo = make_repo(others=[make_other("other", docs={"h2", "h3"})])

    result = get_project_links(links_cmd(), repo=repo)

    assert result == {"comparison": [], "regression": [], "drift": []}


def test_a_single_matching_label_is_not_enough():
    repo = make_repo(others=[make_other("other", labels=["Date"])])

    result = get_project_links(links_cmd(), repo=repo)

    assert result == {"comparison": [], "regression": [], "drift": []}


def test_label_order_and_surrounding_whitespace_do_not_matter():
    repo = make_repo(others=[make_other("other")])

    result = get_project_links(links_cmd(labels=[" Name ", "Date"]), repo=repo)

    assert result["comparison"] == ["other"]


def test_label_case_matters():
    repo = make_repo(others=[make_other("other")])

    result = get_project_links(links_cmd(labels=["date", "name"]), repo=repo)

    assert result == {"comparison": [], "regression": [], "drift": []}


def test_get_project_links_lists_names_sorted():
    repo = make_repo(others=[make_other("b-project"), make_other("a-project")])

    result = get_project_links(links_cmd(), repo=repo)

    assert result["comparison"] == ["a-project", "b-project"]


# --- discard_project ---


def test_discard_project_ignores_project_that_is_already_gone():
    conversion_repo = FakeConversionRepo()
    storage = FakeStorage()

    result = discard_project(
        DiscardProjectCommand(project="new"),
        project_repo=FakeProjectRepo(),
        conversion_repo=conversion_repo,
        storage=storage,
    )

    assert result == {"status": "already_gone"}
    assert conversion_repo.deleted_projects == []
    assert storage.deleted_prefixes == []


def test_discard_project_refuses_project_without_finished_conversion():
    conversion_repo = FakeConversionRepo()
    storage = FakeStorage()

    with pytest.raises(InvalidState) as exc:
        discard_project(
            DiscardProjectCommand(project="new"),
            project_repo=make_repo(conversion_done=()),
            conversion_repo=conversion_repo,
            storage=storage,
        )

    assert exc.value.code == "CONVERSION_NOT_DONE"
    assert conversion_repo.deleted_projects == []
    assert storage.deleted_prefixes == []


def test_discard_project_refuses_project_with_label_studio_project():
    conversion_repo = FakeConversionRepo()
    storage = FakeStorage()

    with pytest.raises(InvalidState) as exc:
        discard_project(
            DiscardProjectCommand(project="new"),
            project_repo=make_repo(label_studio_ids={"new": 5}),
            conversion_repo=conversion_repo,
            storage=storage,
        )

    assert exc.value.code == "PROJECT_ALREADY_HAS_LABEL_STUDIO_ID"
    assert conversion_repo.deleted_projects == []
    assert storage.deleted_prefixes == []


def test_discard_project_deletes_rows_and_storage():
    conversion_repo = FakeConversionRepo()
    storage = FakeStorage()

    result = discard_project(
        DiscardProjectCommand(project="new"),
        project_repo=make_repo(),
        conversion_repo=conversion_repo,
        storage=storage,
    )

    assert result == {"status": "discarded"}
    assert conversion_repo.deleted_projects == ["new"]
    assert conversion_repo.committed is True
    assert storage.deleted_prefixes == ["new"]
