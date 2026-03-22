.PHONY: run migrate migrations seed test lint fmt worker shell db-create db-drop db-reset

PROJECT_NAME ?= saas_boilerplate

run:
	uv run uvicorn config.asgi:application --reload --host 0.0.0.0 --port 8000

migrate:
	uv run python manage.py migrate

migrations:
	uv run python manage.py makemigrations

seed:
	uv run python manage.py seed

shell:
	uv run python manage.py shell_plus

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check .

fmt:
	uv run ruff format . && uv run ruff check --fix .

worker:
	uv run celery -A config worker -l info

db-create:
	createdb $(PROJECT_NAME)

db-drop:
	dropdb --if-exists $(PROJECT_NAME)

db-reset: db-drop db-create migrate seed
