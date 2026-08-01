# orchestrator/domain/ollama.py


import os

from domain.models.ollama import ListModelsCommand, PullModelCommand

ARCHIVE_PREFIX = os.getenv("XTRACTYL_MODEL_ARCHIVE_PREFIX", "xtractyl-archive")


def list_models(cmd: ListModelsCommand, ollama_client, model_repo) -> dict:
    """Only offers models that are BOTH physically present in Ollama's live
    tag list AND tracked in the Postgres `models` table (digest-pinned,
    provenance-recorded via reconcile_models). Matching purely by the
    'xtractyl-archive/' name prefix, as before, would let anyone with
    direct Ollama API access (bypassing reconcile_models entirely) get an
    untracked tag offered in the UI — selectable, but failing later with
    MODEL_NOT_FOUND the moment someone actually tries to use it, since
    enqueue_prelabel_job looks it up via model_repo.get_by_archived_name,
    not Ollama directly."""
    tags = ollama_client.list_tags()
    known_archived_names = model_repo.list_archived_names()
    return {
        "models": [
            name
            for name in ((t.get("model") or t.get("name")) for t in tags)
            if name and name.startswith(f"{ARCHIVE_PREFIX}/") and name in known_archived_names
        ]
    }


def pull_model(cmd: PullModelCommand, ollama_client):
    yield from ollama_client.pull(cmd.model)
