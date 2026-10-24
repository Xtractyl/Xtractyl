.PHONY: deps up down smoke dev-up dev-build dev-restart dev-down

deps:
	python -m pip install -r tests/requirements-test-smoke.txt

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
		worker_prelabel \
		worker_conversion 

down:
	docker compose down 

smoke:
	python -m pytest tests/smoke -v

# --- Unit tests inside the service containers ---
unit-orchestrator:
	docker compose run --rm orchestrator python -m pytest -q tests/unit --cov --cov-config=.coveragerc --cov-report=term-missing

unit-worker_prelabel:
	docker compose run --rm worker_prelabel python -m pytest -q tests/unit  --cov --cov-report=term-missing


unit-worker_conversion:
	docker compose run --rm worker_conversion python -m pytest -q tests/unit --cov --cov-report=term-missing

unit-ml_backend:
	docker compose run --rm ml_backend python -m pytest -q tests/unit --cov --cov-report=term-missing


unit-frontend:
	docker compose run --rm frontend sh -c "npm install && npm run test:coverage"



# --- Dev mode: live code mounts + debugpy (docker-compose.dev.yml) ---
DEV = docker compose -f docker-compose.yml -f docker-compose.dev.yml
DEV_PY_SERVICES = orchestrator ml_backend docling worker_prelabel worker_conversion cleanup
DEV_SERVICES = postgres labelstudio ollama ml_backend orchestrator frontend job_queue \
	postgres_xtractyl minio docling worker_prelabel worker_conversion cleanup

dev-up:
	$(DEV) up -d $(DEV_SERVICES)

# Only needed after changes to requirements or Dockerfiles
dev-build:
	$(DEV) up -d --build $(DEV_SERVICES)

# Apply code changes: make dev-restart [S=orchestrator]; re-attach the debugger afterwards
dev-restart:
	$(DEV) restart $(or $(S),$(DEV_PY_SERVICES))

dev-down:
	$(DEV) down