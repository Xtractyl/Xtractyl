# orchestrator/api/routes/__init__.py

from .health import register as register_health


def register_routes(app):
    register_health(app)
