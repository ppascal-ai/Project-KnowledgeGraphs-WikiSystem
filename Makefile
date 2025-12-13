.PHONY: help venv install run up down docker-run seed test lint format clean logs

help:
	@echo "Commands:"
	@echo "  make venv           Create local virtualenv (.venv)"
	@echo "  make install        Install requirements into .venv"
	@echo "  run         Run API locally"
	@echo "  docker-run  Build & run with docker-compose"
	@echo "  up/down     Start/stop containers"
	@echo "  seed        Seed Neo4j"
	@echo "  test        Run pytest"
	@echo "  lint        Run pylint"
	@echo "  format      Run black"
	@echo "  clean       Clean cache/pyc"

venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		. .venv/bin/activate && pip install --upgrade pip; \
		echo "Created .venv"; \
	else echo ".venv already exists"; fi
	@echo "To activate: source .venv/bin/activate"

install: venv
	@. .venv/bin/activate && pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-run:
	docker-compose up --build -d

up:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f

seed:
	docker-compose exec api python scripts/seed_data.py

test:
	docker-compose exec api pytest

lint:
	docker-compose exec api pylint app --fail-under=9.5

format:
	docker-compose exec api black .

clean:
	rm -rf .pytest_cache .mypy_cache .coverage **/__pycache__