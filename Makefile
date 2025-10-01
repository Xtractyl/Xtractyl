.PHONY: e2e e2e-down

# starts e2e test
e2e:
	./scripts/e2e.sh

# manually ends e2e test
e2e-down:
	docker compose -p e2e -f docker-compose.yml -f docker-compose_test.yml down -v