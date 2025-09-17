.PHONY: install-backend run-backend install-frontend build-frontend dev format test generate-config

install-backend:
	python3 -m pip install -r backend/requirements.txt

run-backend:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

install-frontend:
	@echo "No frontend dependencies to install."

build-frontend:
	bash scripts/generate-config.sh

generate-config: build-frontend

dev: install-backend build-frontend run-backend

format:
	@echo "Add formatting tools if needed."

test:
	@echo "Add tests when available."
