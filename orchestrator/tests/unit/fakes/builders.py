from db.models import PrelabellingRun
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
