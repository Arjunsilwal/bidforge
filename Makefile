.PHONY: help setup install lint format typecheck test train evaluate run-api run-web docker-up docker-down clean

PYTHON ?= python3
VENV ?= .venv

help:
	@echo "BidForge v1 Commands:"
	@echo "  make setup        - Create virtualenv and install dependencies"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code using ruff"
	@echo "  make typecheck    - Run mypy type checker"
	@echo "  make test         - Run pytest test suite"
	@echo "  make train        - Train baseline and quantile cost models"
	@echo "  make evaluate     - Evaluate models on temporal test split"
	@echo "  make run-api      - Launch FastAPI backend server (port 8000)"
	@echo "  make run-web      - Launch Streamlit review workspace (port 8501)"
	@echo "  make docker-up    - Start full containerized stack via docker-compose"
	@echo "  make docker-down  - Stop all docker-compose services"
	@echo "  make clean        - Remove caches and build artifacts"

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "Setup complete. Activate with: source $(VENV)/bin/activate"

install:
	pip install -r requirements.txt

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy api/ ml/ data/

test:
	pytest tests/ -v

train:
	python -m ml.train

evaluate:
	python -m ml.evaluate

run-api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

run-web:
	streamlit run web/app.py --server.port 8501

docker-up:
	docker-compose -f infra/docker-compose.yml up --build -d

docker-down:
	docker-compose -f infra/docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build dist *.egg-info .coverage
