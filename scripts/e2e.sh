#!/usr/bin/env bash
set -euo pipefail

PROJECT=e2e
BASE=docker-compose.yml
TEST=docker-compose_test.yml

echo "[INFO] Starte E2E Tests ..."
docker compose -p "$PROJECT" -f "$BASE" -f "$TEST" up --build --exit-code-from tester tester
EXIT=$?

echo "[INFO] Räume auf ..."
docker compose -p "$PROJECT" -f "$BASE" -f "$TEST" down -v

exit $EXIT