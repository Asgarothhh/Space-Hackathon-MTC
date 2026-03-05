# ═══════════════════════════════════════════════════════════════
# Makefile — управление окружениями прототипирования
#
# Три контура:
#   1. Backend-only   — тесты без фронта
#   2. Frontend-only  — UI с mock API (Prism)
#   3. Full-stack     — E2E тесты
# ═══════════════════════════════════════════════════════════════

.PHONY: help
help: ## Показать справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ─── OpenAPI ────────────────────────────────────────────────────

.PHONY: openapi-export
openapi-export: ## Экспортировать OpenAPI из FastAPI (для сравнения с контрактом)
	python -m scripts.export_openapi --yaml --out openapi-generated

.PHONY: openapi-validate
openapi-validate: ## Проверить дрифт между контрактом и бэкендом
	python -m scripts.validate_contract

.PHONY: openapi-generate-models
openapi-generate-models: ## Генерировать Pydantic-модели из openapi.yaml
	bash scripts/generate_models.sh

.PHONY: openapi-generate-client
openapi-generate-client: ## Генерировать TypeScript API-клиент из openapi.yaml
	bash scripts/generate_client.sh

# ─── Окружение 1: Backend-only ─────────────────────────────────

.PHONY: backend-up
backend-up: ## Поднять бэкенд (PostgreSQL + FastAPI)
	docker compose -f docker-compose.backend.yml up -d postgres-test redis-test backend

.PHONY: backend-down
backend-down: ## Остановить бэкенд
	docker compose -f docker-compose.backend.yml down -v

.PHONY: test
test: ## Запустить unit + интеграционные тесты (локально)
	pytest tests/ -v --tb=short -x

.PHONY: test-docker
test-docker: ## Запустить тесты в Docker (с PostgreSQL)
	docker compose -f docker-compose.backend.yml --profile test run --rm --build tests

.PHONY: test-contract
test-contract: ## Запустить контрактные тесты (schemathesis)
	docker compose -f docker-compose.backend.yml down -v
	docker compose -f docker-compose.backend.yml up -d --build postgres-test redis-test backend
	docker compose -f docker-compose.backend.yml --profile contract run --rm contract-tests

.PHONY: test-contract-local
test-contract-local: ## Контрактные тесты локально (нужен запущенный бэкенд)
	schemathesis run openapi.yaml --url http://localhost:8000 --checks all --max-examples 50

# ─── Окружение 2: Frontend-only ────────────────────────────────

.PHONY: mock-up
mock-up: ## Поднять Prism mock-сервер (для фронтенда)
	docker compose -f docker-compose.frontend.yml up -d

.PHONY: mock-down
mock-down: ## Остановить mock-сервер
	docker compose -f docker-compose.frontend.yml down

.PHONY: mock-local
mock-local: ## Запустить Prism локально (без Docker)
	npx @stoplight/prism-cli mock openapi.yaml --host 0.0.0.0 --port 4010

# ─── Окружение 3: Full-stack ───────────────────────────────────

.PHONY: fullstack-up
fullstack-up: ## Поднять полный стек (бэкенд + БД + Redis)
	docker compose -f docker-compose.fullstack.yml up -d

.PHONY: fullstack-down
fullstack-down: ## Остановить полный стек
	docker compose -f docker-compose.fullstack.yml down -v

.PHONY: test-e2e
test-e2e: ## Запустить E2E-тесты (Playwright)
	docker compose -f docker-compose.fullstack.yml --profile e2e run --rm e2e-tests

# ─── Утилиты ───────────────────────────────────────────────────

.PHONY: lint
lint: ## Линтинг
	ruff check backend/ tests/

.PHONY: format
format: ## Форматирование
	ruff format backend/ tests/

.PHONY: clean
clean: ## Очистить сгенерированные файлы и тестовую БД
	rm -rf generated/models.py generated/api-client/
	rm -f test.db openapi-generated.yaml openapi-generated.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: install-dev
install-dev: ## Установить dev-зависимости
	pip install -r requirments.txt -r requirements-dev.txt
