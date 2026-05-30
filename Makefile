.PHONY: deps up down smoke

deps:
	python -m pip install -r tests/requirements-test.txt

up:
	docker compose up -d \
		postgres \
		labelstudio \
		ollama \
		ml_backend \
		orchestrator \
		frontend \
		job_queue \
		postgres_xtractyl \
		minio \
		worker_prelabel

down:
	docker compose down 

smoke:
	python -m pytest tests/smoke -v

# --- Unit tests inside the service containers ---
unit-orchestrator:
	docker compose run --rm orchestrator python -m pytest -q tests/unit

unit-worker_prelabel:
	docker compose run --rm worker_prelabel python -m pytest -q tests/unit

unit-ml_backend:
	docker compose run --rm ml_backend python -m pytest -q tests/unit