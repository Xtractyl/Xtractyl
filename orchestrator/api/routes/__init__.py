# orchestrator/api/routes/__init__.py

from .evaluation import register as register_evaluation
from .health import register as register_health


def register_routes(app, ok):
    register_health(app)
    register_evaluation(app, ok)
