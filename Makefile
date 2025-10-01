.PHONY: test-smoke test-e2e test-all test-clean

PROJECT ?= testing
COMPOSE_BASE ?= docker-compose.yml
COMPOSE_TEST ?= docker-compose_test.yml

# --- run only SMOKE tests ---
test-smoke:
	@set -e; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) \
		--profile smoke up --build --exit-code-from tester-smoke tester-smoke; \
	EXIT=$$?; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) down -v; \
	exit $$EXIT

# --- run only E2E tests ---
test-e2e:
	@set -e; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) \
		--profile e2e up --build --exit-code-from tester-e2e tester-e2e; \
	EXIT=$$?; \
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) down -v; \
	exit $$EXIT

# --- run SMOKE then E2E sequentially (both must pass) ---
test-all:
	@$(MAKE) test-smoke
	@$(MAKE) test-e2e

# --- manual cleanup if a run was interrupted ---
test-clean:
	docker compose -p $(PROJECT) -f $(COMPOSE_BASE) -f $(COMPOSE_TEST) down -v