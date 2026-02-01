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
		frontend

down:
	docker compose down 

smoke:
	python -m pytest -q tests/smoke