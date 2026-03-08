# orchestrator/api/routes/__init__.py

from .evaluation import register as register_evaluation
from .evaluation_drift import register as register_evaluation_drift
from .health import register as register_health
from .jobs import register as register_jobs
from .projects import register as register_projects
from .results import register as register_results


def register_routes(app, ok, spec):
    register_health(app)
    register_evaluation(app, spec)
    register_evaluation_drift(app, ok, spec)
    register_jobs(app, ok)
    register_results(app, spec)
    register_projects(app, ok)
