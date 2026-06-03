dev:
	uv run uvicorn core.asgi:application --reload --port 8000

prod:
	uv run gunicorn -c core/gunicorn_config.py

celery:
	trap 'kill 0' INT TERM; \
	uv run celery -A core worker -l info & \
	uv run celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler & \
	wait

migrations:
	uv run manage.py makemigrations

migrate: migrations
	uv run manage.py migrate

superuser:
	uv run manage.py createsuperuser

shell:
	uv run manage.py shell

shell_plus:
	uv run manage.py shell_plus

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run ty check

# Install git pre-commit hooks (run once after cloning).
hooks-install:
	uv run pre-commit install

# Run all pre-commit hooks against every file.
hooks:
	uv run pre-commit run --all-files

# Run every static check (lint + format verification + types) without mutating files.
check: lint format-check typecheck

# Backwards-compatible alias kept for existing tooling/CI.
test: lint

messages: ## Generate translation messages
	uv run manage.py makemessages -l ar

compilemessages: ## Compile translation messages
	uv run manage.py compilemessages

.PHONY: clean
clean: ## Remove compiled files and debris
	uv run pyclean . --debris

check:
	uv run manage.py check
check-prod:
	uv run manage.py check --deploy
