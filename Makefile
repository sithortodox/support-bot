.PHONY: test lint format clean install docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests with coverage"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean cache and artifacts"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make migrate      - Run database migrations"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest --cov=. --cov-report=term-missing --cov-report=html -v

test-fast:
	pytest -v --tb=short

lint:
	ruff check .
	black --check .

format:
	black .
	ruff check --fix .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-reset:
	docker-compose down -v
	docker-compose up -d

coverage:
	pytest --cov=. --cov-report=html
	open htmlcov/index.html || xdg-open htmlcov/index.html

check: lint test
	@echo "All checks passed!"
