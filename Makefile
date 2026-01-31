.PHONY: deps up down smoke

deps:
	python -m pip install -r tests/requirements-test.txt

up:
	docker compose up -d orchestrator

down:
	docker compose down -v

smoke:
	python -m pytest -q tests/smoke