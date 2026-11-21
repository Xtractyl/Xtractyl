.PHONY: deps up down smoke dev-up dev-build dev-restart dev-down fhir-synthea-regen \
	fhir-generate fhir-synthea-prune fhir-check

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


# --- FHIR test data (see docs/fhir-test-server.md) ---
# Maintainer targets, not needed for normal use: the results are committed.
#   1. fhir-synthea-regen  raw Synthea bundles -> fhir_seed/data/synthea/
#                          (builds only the Synthea stage, no local Java needed;
#                          refuses to replace an existing set unless FORCE=1,
#                          because the document bundles were built from it)
#   2. fhir-generate       document bundles without texts
#                          -> fhir_seed/data/document_bundle_generated/ (git-ignored)
#                          and copies NEW ones to document_bundle_final/
#                          (existing files there are never overwritten)
#   3. write the section texts directly in fhir_seed/data/document_bundle_final/*.json
#   4. fhir-check          validates document_bundle_final/ before committing

FHIR_DATA := fhir_seed/data
FHIR_GENERATED := $(FHIR_DATA)/document_bundle_generated
FHIR_FINAL := $(FHIR_DATA)/document_bundle_final
FHIR_SYNTHEA_PATIENT_COUNT ?= 300
FHIR_SYNTHEA_SEED ?= 12345

fhir-synthea-regen:
	@if ls $(FHIR_DATA)/synthea/*.json >/dev/null 2>&1 && [ -z "$(FORCE)" ]; then \
		echo "$(FHIR_DATA)/synthea already contains bundles; documents were built from them."; \
		echo "Run 'make fhir-synthea-regen FORCE=1' to replace them."; \
		exit 1; \
	fi
	rm -rf $(FHIR_DATA)/synthea
	docker build -f docker/fhir_seed/Dockerfile --target synthea_export \
		--build-arg FHIR_SYNTHEA_PATIENT_COUNT=$(FHIR_SYNTHEA_PATIENT_COUNT) \
		--build-arg FHIR_SYNTHEA_SEED=$(FHIR_SYNTHEA_SEED) \
		--output type=local,dest=$(FHIR_DATA)/synthea .

fhir-generate:
	python fhir_seed/build_documents.py $(FHIR_DATA)/synthea $(FHIR_GENERATED)
	mkdir -p $(FHIR_FINAL)
	@for f in $(FHIR_GENERATED)/*.json; do \
		[ -e "$$f" ] || continue; \
		[ -e "$(FHIR_FINAL)/$$(basename "$$f")" ] || cp "$$f" $(FHIR_FINAL)/; \
	done

fhir-synthea-prune:
	@ls $(FHIR_GENERATED)/*.json >/dev/null 2>&1 || { \
		echo "No bundles in $(FHIR_GENERATED); run 'make fhir-generate' first."; \
		exit 1; \
	}
	@keep=$$(ls $(FHIR_GENERATED) | sed 's/__.*/.json/' | sort -u); \
	for f in $(FHIR_DATA)/synthea/*.json; do \
		b=$$(basename "$$f"); \
		case "$$b" in hospitalInformation*|practitionerInformation*) continue ;; esac; \
		echo "$$keep" | grep -Fxq "$$b" || { rm "$$f"; echo "removed $$b"; }; \
	done

fhir-check:
	python fhir_seed/check_documents.py $(FHIR_FINAL)