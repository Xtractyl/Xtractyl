# orchestrator/domain/evaluation_views.py

from itertools import combinations

from domain.evaluation import _entry_to_dict


def get_regression_view(
    project_name: str, project_repo, run_repo, model_repo, eval_repo, scope: str = "external"
) -> dict:
    """Same documents, same labels, same questions, same model, same
    system prompt — only time varies. Driven by the picked project's own
    run configuration, not by resolving one canonical groundtruth project
    first. For scope="internal", the resulting points can legitimately
    come from *different* internal-GT projects sharing this exact
    configuration, each contributing at most one point — not "the same
    groundtruth set over time" the way external regression traditionally
    worked, but "how this configuration performed across independent
    internal reviews over time"."""
    run = run_repo.get_latest_run(project_name)
    if not run:
        return {"entries": []}

    model = model_repo.get_by_id(run.model_id)
    if not model:
        return {"entries": []}

    finder = (
        eval_repo.find_internal_evaluations_by_configuration
        if scope == "internal"
        else eval_repo.find_external_evaluations_by_configuration
    )
    matching = finder(
        labels_hash=run.labels_hash,
        questions_hash=run.questions_hash,
        model_digest=model.digest,
        system_prompt_hash=run.system_prompt_hash,
    )

    # Regression means "same documents, only time varies" — find_*_evaluations_by_configuration
    # only filters on labels/questions/model/prompt, not document set, since Drift (the other
    # caller of these methods) deliberately needs matches across *different* document sets. This
    # post-filter restores the document-set constraint for Regression specifically: an evaluation
    # only counts here if its GT's document_set_hash matches the picked project's own — same rule
    # for both scopes, so multiple internal-GT projects can appear together exactly when (and only
    # when) they genuinely share identical documents, not merely the same configuration.
    own_project = project_repo.get_project(project_name)
    own_docset = own_project.document_set_hash if own_project else None
    matching = [
        e
        for e in matching
        if (gt := project_repo.get_project(e.groundtruth_project))
        and gt.document_set_hash == own_docset
    ]

    if len(matching) < 2:
        return {"entries": []}

    ordered = sorted(matching, key=lambda e: e.run_at or e.created_at)
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
    return {"entries": entries}


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


def get_drift_view(
    project_name: str, project_repo, run_repo, model_repo, eval_repo, scope: str = "external"
) -> dict:
    """Same labels, same questions, same model, same system prompt — but
    the document set differs, with ZERO overlap between individual
    document hashes — not just an unequal aggregate hash (a 40/41-identical
    set would have a different aggregate hash but shouldn't count as
    genuine drift).

    Driven by the picked project's own run configuration, same as
    Regression — any picked project, not just a GT itself, can anchor the
    search. Because overlap-freedom isn't transitive, there is no single
    "the" group once more than two document sets share a configuration —
    this returns the one true, longest overlap-free chain containing the
    picked project's own document set."""
    run = run_repo.get_latest_run(project_name)
    if not run:
        return {"entries": []}

    model = model_repo.get_by_id(run.model_id)
    if not model:
        return {"entries": []}

    finder = (
        eval_repo.find_internal_evaluations_by_configuration
        if scope == "internal"
        else eval_repo.find_external_evaluations_by_configuration
    )
    matching = finder(
        labels_hash=run.labels_hash,
        questions_hash=run.questions_hash,
        model_digest=model.digest,
        system_prompt_hash=run.system_prompt_hash,
    )

    # Dedup by document_set_hash, keeping the newest evaluation per unique document set —
    # deliberate, not accidental: `matching` is ordered ascending by run_at, and this uses a
    # plain assignment (not setdefault), so each later (newer) evaluation for an already-seen
    # document set overwrites the earlier one, leaving the most recent as representative.
    # The document set's hash is looked up via e.groundtruth_project, not via the comparison
    # run's own project — not because the two would differ (evaluate_run's HTML_HASH_MISMATCH
    # guard, see Evaluation Pipeline, guarantees the GT's document set and the evaluated run's
    # own project's document set are always identical whenever an Evaluation exists at all),
    # but because it's the cheaper lookup path: one project_repo.get_project() call, versus a
    # run_repo.get_run() -> project_repo.get_project() detour via the comparison run.
    by_docset: dict[str, object] = {}
    for e in matching:
        gt = project_repo.get_project(e.groundtruth_project)
        by_docset[gt.document_set_hash] = e

    own_project = project_repo.get_project(project_name)
    own_key = own_project.document_set_hash if own_project else None
    if own_key not in by_docset or len(by_docset) < 2:
        return {"entries": []}

    # Determine our own GT name directly — never derive it from whichever evaluation happened
    # to win the document_set_hash dedup above. Internal GTs have no uniqueness guarantee on
    # document_set_hash (unlike external): a different internal-GT project could coincidentally
    # share the same hash and have a newer evaluation, silently taking over that dict slot and
    # making the dedup step above pick the wrong project's evaluation as the representative for
    # our own document set.
    if project_repo.get_groundtruth_scope(project_name) != "none":
        own_gt_name = project_name
    else:
        own_gt_name = next(
            (
                e.groundtruth_project
                for e in matching
                if (r := run_repo.get_run(e.comparison_prelabelling_run_id))
                and r.project == project_name
            ),
            None,
        )
    if not own_gt_name:
        return {"entries": []}

    # Only the deduplicated, unique document sets go through the expensive pairwise overlap
    # check — but our own GT must always be a candidate, even if it lost the dedup above to a
    # different, newer evaluation sharing the same document_set_hash (see comment above).
    by_gt: dict[str, object] = {e.groundtruth_project: e for e in by_docset.values()}
    if own_gt_name not in by_gt:
        by_gt[own_gt_name] = next(e for e in matching if e.groundtruth_project == own_gt_name)
    names = list(by_gt.keys())
    html_hash_sets = {name: project_repo.get_html_hashes_for_project(name) for name in names}
    compatible: dict[str, set] = {n: set() for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if not (html_hash_sets[a] & html_hash_sets[b]):
                compatible[a].add(b)
                compatible[b].add(a)

    created_at = {name: (project_repo.get_project(name).created_at or "") for name in names}
    chain = _find_best_drift_chain(names, compatible, created_at, must_include=own_gt_name)
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
