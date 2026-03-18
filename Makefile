.PHONY: install dev-install migrate worker beat test lint

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt

infra:
	docker compose up -d

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

worker:
	celery -A src.celery_app worker --loglevel=info

beat:
	celery -A src.celery_app beat --loglevel=info

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/
