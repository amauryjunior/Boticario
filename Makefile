# Inclua Beauty AI — atalhos de desenvolvimento e deploy.
.PHONY: help install test lint dev-backend dev-frontend build-frontend \
        migrate deploy tf-plan tf-destroy

help:
	@echo "Alvos disponíveis:"
	@echo "  make install         instala backend (venv) e frontend"
	@echo "  make test            roda pytest do backend"
	@echo "  make lint            roda ruff no backend"
	@echo "  make dev-backend     sobe a API (uvicorn --reload)"
	@echo "  make dev-frontend    sobe o frontend (vite)"
	@echo "  make migrate         aplica migrations (alembic upgrade head)"
	@echo "  make deploy          deploy completo no GCP (ver scripts/deploy.sh)"
	@echo "  make tf-plan         terraform plan"
	@echo "  make tf-destroy      terraform destroy"

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm install

test:
	cd backend && . .venv/bin/activate && pytest

lint:
	cd backend && . .venv/bin/activate && ruff check .

dev-backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

deploy:
	./scripts/deploy.sh

tf-plan:
	terraform -chdir=infra/terraform init -input=false
	terraform -chdir=infra/terraform plan

tf-destroy:
	terraform -chdir=infra/terraform destroy
