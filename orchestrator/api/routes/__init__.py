# orchestrator/api/routes/__init__.py

from .conversion import register as register_conversion
from .evaluation import register as register_evaluation
from .evaluation_views import register as register_evaluation_views
from .health import register as register_health
from .jobs import register as register_jobs
from .ollama import register as register_ollama
from .projects import register as register_projects
from .results import register as register_results


def register_routes(app, spec, storage, queue, session_factory, label_studio, ollama_client):
    register_health(app)
    register_conversion(app, spec, storage=storage, queue=queue, session_factory=session_factory)
    register_evaluation(app, spec, session_factory=session_factory)
    register_evaluation_views(app, spec, session_factory=session_factory)
    register_jobs(app, spec, session_factory=session_factory)
    register_results(app, spec, session_factory=session_factory)
    register_projects(
        app, spec, session_factory=session_factory, label_studio=label_studio, storage=storage
    )
    register_ollama(app, spec, session_factory=session_factory, ollama_client=ollama_client)
