#!/usr/bin/env bash
set -euo pipefail

PROJECT=e2e
BASE=docker-compose.yml
TEST=docker-compose_test.yml

echo "[INFO] Starting E2E Tests ..."
docker compose -p "$PROJECT" -f "$BASE" -f "$TEST" up --build --exit-code-from tester tester
EXIT=$?

echo "[INFO] Cleaning after E2E Tests ..."
docker compose -p "$PROJECT" -f "$BASE" -f "$TEST" down -v

exit $EXIT