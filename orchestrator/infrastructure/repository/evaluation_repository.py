# orchestrator/infrastructure/repository/evaluation_repository.py

from db.models import Evaluation, Model, PrelabellingRun
from infrastructure.interfaces.repository import EvaluationRepositoryInterface


class EvaluationRepository(EvaluationRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def save_evaluation(
        self,
        groundtruth_project: str,
        comparison_prelabelling_run_id: int,
        run_at: str,
        metrics_micro: dict,
        metrics_per_label: dict,
        filenames_count: int,
        task_metrics: list | None = None,
        performance: dict | None = None,
        labels: list | None = None,
    ) -> int:
        evaluation = Evaluation(
            groundtruth_project=groundtruth_project,
            comparison_prelabelling_run_id=comparison_prelabelling_run_id,
            run_at=run_at,
            metrics_micro=metrics_micro,
            metrics_per_label=metrics_per_label,
            filenames_count=filenames_count,
            task_metrics=task_metrics,
            performance=performance,
            labels=labels,
        )
        self._db.add(evaluation)
        self._db.flush()
        self._db.refresh(evaluation)
        return evaluation.id

    def get_evaluations_by_groundtruth_project(self, groundtruth_project: str) -> list:
        return (
            self._db.query(Evaluation)
            .filter(Evaluation.groundtruth_project == groundtruth_project)
            .order_by(Evaluation.run_at)
            .all()
        )

    def find_evaluations_by_configuration(
        self, labels_hash: str, questions_hash: str, model_digest: str, system_prompt_hash: str
    ) -> list:
        """Backs both Regression and Drift: same (labels, questions, model,
        prompt) — they only differ in how the result is grouped afterwards.
        Compares system_prompt_hash rather than raw system_prompt text."""
        return (
            self._db.query(Evaluation)
            .join(PrelabellingRun, PrelabellingRun.id == Evaluation.comparison_prelabelling_run_id)
            .join(Model, Model.id == PrelabellingRun.model_id)
            .filter(
                PrelabellingRun.labels_hash == labels_hash,
                PrelabellingRun.questions_hash == questions_hash,
                PrelabellingRun.system_prompt_hash == system_prompt_hash,
                Model.digest == model_digest,
            )
            .order_by(Evaluation.run_at)
            .all()
        )

    def find_evaluation_for_run(self, run_id: int):
        """Given a run_id alone, find any evaluation for it. Under the
        uq_groundtruth_labels_documents constraint, a run can match at most
        one external groundtruth project, so "any" is, in practice, "the
        one". Backs resolve_family_for_project in domain/evaluation.py."""
        return (
            self._db.query(Evaluation)
            .filter(Evaluation.comparison_prelabelling_run_id == run_id)
            .first()
        )

    def list_projects_with_evaluations(self) -> list[str]:
        """Backs GET /evaluations/projects: every project name involved in
        at least one Evaluation row — either as groundtruth_project, or as
        the project of the evaluated run."""
        gt_names = {r[0] for r in self._db.query(Evaluation.groundtruth_project).distinct().all()}
        run_project_names = {
            r[0]
            for r in (
                self._db.query(PrelabellingRun.project)
                .join(Evaluation, Evaluation.comparison_prelabelling_run_id == PrelabellingRun.id)
                .distinct()
                .all()
            )
        }
        return sorted(gt_names | run_project_names)
