import json
import logging
import os

from flask import jsonify, request

# Fixed base dir (no env lookups)
BASE_PROJECTS_DIR = os.path.join("data", "projects")

logger = logging.getLogger(__name__)


def _safe_join(base: str, *paths: str) -> str:
    """Prevent path traversal by resolving and checking commonprefix."""
    full = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if not os.path.commonprefix([full, base_abs]) == base_abs:
        raise ValueError("Invalid path")
    return full


def list_projects_route():
    """
    GET /list_projects
    Returns: ["ProjectA", "ProjectB", ...]
    Lists folders directly under data/projects.
    """
    try:
        if not os.path.isdir(BASE_PROJECTS_DIR):
            return jsonify([]), 200
        items = sorted(
            d
            for d in os.listdir(BASE_PROJECTS_DIR)
            if os.path.isdir(os.path.join(BASE_PROJECTS_DIR, d))
        )
        return jsonify(items), 200
    except Exception as e:
        logger.exception("Failed to list projects")
        return jsonify({"error": str(e)}), 500


def list_qal_jsons_route():
    """
    GET /list_qal_jsons?project=<name>
    Returns: ["questions_and_labels.json", ...]
    Lists *.json files in the project's folder.
    """
    project = (request.args.get("project") or "").strip()
    if not project:
        return jsonify({"error": "missing 'project'"}), 400

    try:
        project_dir = _safe_join(BASE_PROJECTS_DIR, project)
        if not os.path.isdir(project_dir):
            return jsonify([]), 200

        files = sorted(
            f
            for f in os.listdir(project_dir)
            if f.lower().endswith(".json") and os.path.isfile(os.path.join(project_dir, f))
        )
        return jsonify(files), 200
    except ValueError:
        return jsonify({"error": "invalid path"}), 400
    except Exception as e:
        logger.exception("Failed to list JSON files")
        return jsonify({"error": str(e)}), 500


def preview_qal_route():
    """
    GET /preview_qal?project=<name>&file=<filename.json>
    Returns: parsed JSON of the file (object or array).
    """
    project = (request.args.get("project") or "").strip()
    filename = (request.args.get("file") or "").strip()
    if not project or not filename:
        return jsonify({"error": "missing 'project' or 'file'"}), 400
    if not filename.lower().endswith(".json"):
        return jsonify({"error": "file must be a .json"}), 400

    try:
        project_dir = _safe_join(BASE_PROJECTS_DIR, project)
        file_path = _safe_join(project_dir, filename)
        if not os.path.isfile(file_path):
            return jsonify({"error": "file not found"}), 404

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except ValueError:
        return jsonify({"error": "invalid path"}), 400
    except json.JSONDecodeError:
        return jsonify({"error": "invalid JSON"}), 400
    except Exception as e:
        logger.exception("Failed to preview JSON")
        return jsonify({"error": str(e)}), 500
