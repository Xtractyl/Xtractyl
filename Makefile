.PHONY: test-e2e test-smoke
PROJECT ?= testing
COMPOSE_BASE ?= docker-compose.yml
COMPOSE_TEST ?= docker-compose_test.yml
LOG_DIR ?= logs_testing
RUN_ID ?= $(shell date -u +%Y%m%dT%H%M%SZ)

test-e2e:
	@set -e; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) up -d --build; \
	EXIT=0; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) run --rm -e RUN_ID=$(RUN_ID) tester-e2e || EXIT=$$?; \
	mkdir -p $(LOG_DIR)/e2e/$(RUN_ID); \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) ps > $(LOG_DIR)/e2e/$(RUN_ID)/ps.txt 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color orchestrator > $(LOG_DIR)/e2e/$(RUN_ID)/orchestrator.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color docling > $(LOG_DIR)/e2e/$(RUN_ID)/docling.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color labelstudio > $(LOG_DIR)/e2e/$(RUN_ID)/labelstudio.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color postgres > $(LOG_DIR)/e2e/$(RUN_ID)/postgres.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) down -v --remove-orphans || true; \
	exit $$EXIT

test-smoke:
	@set -e; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) up -d --build; \
	EXIT=0; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) run --rm -e RUN_ID=$(RUN_ID) tester-smoke || EXIT=$$?; \
	mkdir -p $(LOG_DIR)/smoke/$(RUN_ID); \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) ps > $(LOG_DIR)/smoke/$(RUN_ID)/ps.txt 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color orchestrator > $(LOG_DIR)/smoke/$(RUN_ID)/orchestrator.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color docling > $(LOG_DIR)/smoke/$(RUN_ID)/docling.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color labelstudio > $(LOG_DIR)/smoke/$(RUN_ID)/labelstudio.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) logs --no-color postgres > $(LOG_DIR)/smoke/$(RUN_ID)/postgres.log 2>&1 || true; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) down -v --remove-orphans || true; \
	exit $$EXIT