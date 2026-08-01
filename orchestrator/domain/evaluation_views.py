# orchestrator/domain/evaluation_views.py

from itertools import combinations

from domain.evaluation import _entry_to_dict, resolve_family_for_project


def get_regression_view(project_name: str, project_repo, run_repo, model_repo, eval_repo) -> dict:
    """Same documents, same labels, same questions, same model, same
    system prompt — only time varies. Since a project's document set
    uniquely identifies its groundtruth project, multiple regression
    points can only come from *other* projects evaluated against this
    exact same groundtruth project with this exact same configuration."""
    groundtruth_project, run = resolve_family_for_project(
        project_name, project_repo, run_repo, eval_repo
    )
    if not groundtruth_project or not run:
        return {"groundtruth_project": None, "entries": []}

    model = model_repo.get_by_id(run.model_id)
    if not model:
        return {"groundtruth_project": groundtruth_project, "entries": []}

    matching = eval_repo.find_evaluations_by_configuration(
        labels_hash=run.labels_hash,
        questions_hash=run.questions_hash,
        model_digest=model.digest,
        system_prompt_hash=run.system_prompt_hash,
    )
    same_gt = [e for e in matching if e.groundtruth_project == groundtruth_project]
    if len(same_gt) < 2:
        return {"groundtruth_project": groundtruth_project, "entries": []}

    ordered = sorted(same_gt, key=lambda e: e.run_at or e.created_at)
    entries = []
    for e in ordered:
        entry_run = run_repo.get_run(e.comparison_prelabelling_run_id)
        entry_model = model_repo.get_by_id(entry_run.model_id) if entry_run else None
        entries.append(
            _entry_to_dict(
                e,
                entry_model.archived_name if entry_model else None,
                entry_run.project if entry_run else None,
            )
        )
    return {"groundtruth_project": groundtruth_project, "entries": entries}


def _is_clique(combo: tuple, compatible: dict[str, set]) -> bool:
    combo_set = set(combo)
    return all(compatible[a] >= (combo_set - {a}) for a in combo)


def _find_best_drift_chain(names, compatible, created_at, must_include) -> tuple:
    """Maximum-clique search over the pairwise-overlap-free compatibility
    graph, restricted to chains containing must_include. Brute force via
    itertools.combinations, descending by size — deliberately simple:
    the graph stays small since candidates are pre-filtered to one
    configuration already.

    Tie-break: among chains of equal (maximum) size, prefer the one whose
    most recent member is the youngest."""
    n = len(names)
    for size in range(n, 0, -1):
        candidates = [
            combo
            for combo in combinations(names, size)
            if must_include in combo and _is_clique(combo, compatible)
        ]
        if candidates:
            return max(candidates, key=lambda combo: max(created_at[c] for c in combo))
    return (must_include,)


def get_drift_view(project_name: str, project_repo, run_repo, model_repo, eval_repo) -> dict:
    """Same labels, same questions, same model, same system prompt — but
    the groundtruth project (and its document set) differs, with ZERO
    overlap between individual document hashes — not just an unequal
    aggregate hash (a 40/41-identical set would have a different aggregate
    hash but shouldn't count as genuine drift).

    Because overlap-freedom isn't transitive, there is no single "the"
    group once more than two groundtruth projects share a configuration —
    this returns the one true, longest overlap-free chain containing the
    picked project."""
    groundtruth_project, run = resolve_family_for_project(
        project_name, project_repo, run_repo, eval_repo
    )
    if not groundtruth_project or not run:
        return {"entries": []}

    model = model_repo.get_by_id(run.model_id)
    if not model:
        return {"entries": []}

    matching = eval_repo.find_evaluations_by_configuration(
        labels_hash=run.labels_hash,
        questions_hash=run.questions_hash,
        model_digest=model.digest,
        system_prompt_hash=run.system_prompt_hash,
    )
    by_gt: dict[str, object] = {}
    for e in matching:
        by_gt.setdefault(e.groundtruth_project, e)

    if groundtruth_project not in by_gt or len(by_gt) < 2:
        return {"entries": []}

    names = list(by_gt.keys())
    html_hash_sets = {name: project_repo.get_html_hashes_for_project(name) for name in names}
    compatible: dict[str, set] = {n: set() for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if not (html_hash_sets[a] & html_hash_sets[b]):
                compatible[a].add(b)
                compatible[b].add(a)

    created_at = {name: (project_repo.get_project(name).created_at or "") for name in names}
    chain = _find_best_drift_chain(names, compatible, created_at, must_include=groundtruth_project)
    if len(chain) < 2:
        return {"entries": []}

    ordered_names = sorted(chain, key=lambda n: created_at[n])
    entries = []
    for name in ordered_names:
        e = by_gt[name]
        entry_run = run_repo.get_run(e.comparison_prelabelling_run_id)
        entry_model = model_repo.get_by_id(entry_run.model_id) if entry_run else None
        entries.append(
            {
                **_entry_to_dict(
                    e,
                    entry_model.archived_name if entry_model else None,
                    entry_run.project if entry_run else None,
                ),
                "groundtruth_project": name,
            }
        )
    return {"entries": entries}
