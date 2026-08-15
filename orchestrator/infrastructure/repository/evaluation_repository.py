# orchestrator/infrastructure/repository/evaluation_repository.py

from db.models import Evaluation, Model, PrelabellingRun, Project
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

    def find_internal_evaluations_by_labels_and_document_set(
        self, labels_hash: str, document_set_hash: str
    ) -> list:
        """Every internal-groundtruth evaluation sharing this exact labels
        + document set — potentially many, one per matching internal GT
        project (each self-contained, no cross-project ambiguity)."""
        return (
            self._db.query(Evaluation)
            .join(Project, Project.name == Evaluation.groundtruth_project)
            .filter(
                Project.groundtruth == "internal",
                Project.labels_hash == labels_hash,
                Project.document_set_hash == document_set_hash,
            )
            .order_by(Evaluation.run_at)
            .all()
        )

    def find_internal_evaluations_by_configuration(
        self, labels_hash: str, questions_hash: str, model_digest: str, system_prompt_hash: str
    ) -> list:
        """Same as above, but filtered to the exact configuration (used by
        Regression and Drift) rather than just labels + document set."""
        return (
            self._db.query(Evaluation)
            .join(Project, Project.name == Evaluation.groundtruth_project)
            .join(PrelabellingRun, PrelabellingRun.id == Evaluation.comparison_prelabelling_run_id)
            .join(Model, Model.id == PrelabellingRun.model_id)
            .filter(
                Project.groundtruth == "internal",
                PrelabellingRun.labels_hash == labels_hash,
                PrelabellingRun.questions_hash == questions_hash,
                PrelabellingRun.system_prompt_hash == system_prompt_hash,
                Model.digest == model_digest,
            )
            .order_by(Evaluation.run_at)
            .all()
        )

    def find_external_evaluations_by_labels_and_document_set(
        self, labels_hash: str, document_set_hash: str
    ) -> list:
        """External-groundtruth equivalent of the internal method above.
        No separate groundtruth_project filter needed:
        uq_external_groundtruth_labels_documents guarantees at most one
        external GT can ever match this labels + document set anyway."""
        return (
            self._db.query(Evaluation)
            .join(Project, Project.name == Evaluation.groundtruth_project)
            .filter(
                Project.groundtruth == "external",
                Project.labels_hash == labels_hash,
                Project.document_set_hash == document_set_hash,
            )
            .order_by(Evaluation.run_at)
            .all()
        )

    def find_external_evaluations_by_configuration(
        self, labels_hash: str, questions_hash: str, model_digest: str, system_prompt_hash: str
    ) -> list:
        """External equivalent of find_internal_evaluations_by_configuration."""
        return (
            self._db.query(Evaluation)
            .join(Project, Project.name == Evaluation.groundtruth_project)
            .join(PrelabellingRun, PrelabellingRun.id == Evaluation.comparison_prelabelling_run_id)
            .join(Model, Model.id == PrelabellingRun.model_id)
            .filter(
                Project.groundtruth == "external",
                PrelabellingRun.labels_hash == labels_hash,
                PrelabellingRun.questions_hash == questions_hash,
                PrelabellingRun.system_prompt_hash == system_prompt_hash,
                Model.digest == model_digest,
            )
            .order_by(Evaluation.run_at)
            .all()
        )

    def find_evaluation(self, groundtruth_project: str, run_id: int):
        # Backs the get-or-compute path in /evaluate-ai: check whether
        # sync_missing_evaluations already produced this evaluation.
        return (
            self._db.query(Evaluation)
            .filter(
                Evaluation.groundtruth_project == groundtruth_project,
                Evaluation.comparison_prelabelling_run_id == run_id,
            )
            .first()
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
