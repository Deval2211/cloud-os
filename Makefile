# Cloud OS - Makefile
# Common development commands

.PHONY: help up down logs test lint format clean install dev-setup

help:
	@echo "Cloud OS - Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev-setup    - Complete dev setup"
	@echo ""
	@echo "Docker:"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Watch logs (all services)"
	@echo ""
	@echo "Backend:"
	@echo "  make backend-logs - Watch backend logs"
	@echo "  make backend-shell- Access backend container"
	@echo "  make migrate      - Run database migrations"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-logs- Watch frontend logs"
	@echo "  make frontend-shell-Access frontend container"
	@echo ""
	@echo "Database:"
	@echo "  make db-shell     - Access PostgreSQL"
	@echo "  make db-reset     - Reset database"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make test         - Run tests"
	@echo "  make test-watch   - Run tests in watch mode"

install:
	@echo "Installing dependencies..."
	cd src/frontend && npm install

dev-setup: install
	@echo "Setting up development environment..."
	cp .env.example .env
	docker-compose build
	docker-compose up -d
	@echo "✓ Development environment ready!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

up:
	docker-compose up -d
	@echo "✓ Services started"

down:
	docker-compose down
	@echo "✓ Services stopped"

logs:
	docker-compose logs -f

backend-logs:
	docker-compose logs -f backend

backend-shell:
	docker-compose exec backend bash

frontend-logs:
	docker-compose logs -f frontend

frontend-shell:
	docker-compose exec frontend sh

db-shell:
	docker-compose exec postgres psql -U postgres -d cloud_os

db-reset:
	@echo "Resetting database..."
	docker-compose exec backend python -m db.init_db
	@echo "✓ Database reset"

migrate:
	@echo "Running migrations..."
	docker-compose exec backend alembic upgrade head
	@echo "✓ Migrations complete"

lint:
	@echo "Running linters..."
	docker-compose exec backend flake8 .
	docker-compose exec frontend npm run lint
	@echo "✓ Linting complete"

format:
	@echo "Formatting code..."
	docker-compose exec backend black .
	docker-compose exec backend isort .
	docker-compose exec frontend npm run format
	@echo "✓ Formatting complete"

test:
	@echo "Running tests..."
	docker-compose exec backend pytest
	@echo "✓ Tests complete"

test-watch:
	@echo "Running tests in watch mode..."
	docker-compose exec backend pytest -v --tb=short -s

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	docker-compose down -v
	@echo "✓ Cleanup complete"

# Convenience shortcuts
s: up
st: down
l: logs
t: test
f: format

.DEFAULT_GOAL := help
