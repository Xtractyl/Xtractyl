# orchestrator/tests/unit/fakes/builders.py
from db.models import PrelabellingRun, PrelabellingRunTask
from utils.hashing import compute_system_prompt_hash


def make_run(status, model_id=1, system_prompt="Extract.", project="proj", run_id=1):
    return PrelabellingRun(
        id=run_id,
        project=project,
        model_id=model_id,
        system_prompt=system_prompt,
        system_prompt_hash=compute_system_prompt_hash(system_prompt),
        status=status,
    )


def make_task(
    filename,
    label_studio_task_id,
    raw_llm_answers=None,
    status="success",
    run_id=1,
    task_id=1,
):
    return PrelabellingRunTask(
        id=task_id,
        prelabelling_run_id=run_id,
        filename=filename,
        label_studio_task_id=label_studio_task_id,
        status=status,
        raw_llm_answers=raw_llm_answers,
    )
