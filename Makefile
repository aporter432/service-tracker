# Makefile for ORBCOMM Service Tracker
# Provides common development and deployment commands

.PHONY: help install install-dev test lint format clean run docker-build docker-up deploy-heroku deploy-gcp

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)ORBCOMM Service Tracker - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install production dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements-prod.txt
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

setup: ## Run initial setup
	@echo "$(BLUE)Running setup script...$(NC)"
	./scripts/setup.sh

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=orbcomm_tracker --cov-report=html --cov-report=term

lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check --diff .
	isort --check-only --diff .

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	safety check || true
	bandit -r orbcomm_tracker/ || true

clean: ## Clean up temporary files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml
	@echo "$(GREEN)✅ Cleaned up$(NC)"

run: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	python3 orbcomm_dashboard.py

run-prod: ## Run production server with gunicorn
	@echo "$(BLUE)Starting production server...$(NC)"
	gunicorn --config gunicorn.conf.py wsgi:application

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t orbcomm-tracker:latest .
	@echo "$(GREEN)✅ Docker image built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Containers started$(NC)"
	@echo "Access at: http://localhost:5000"

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Containers stopped$(NC)"

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-dev: ## Start development Docker environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml up --build

deploy: ## Interactive deployment menu
	@echo "$(BLUE)Starting deployment...$(NC)"
	./scripts/deploy.sh

deploy-heroku: ## Deploy to Heroku
	@echo "$(BLUE)Deploying to Heroku...$(NC)"
	./scripts/deploy.sh heroku

deploy-gcp: ## Deploy to Google Cloud
	@echo "$(BLUE)Deploying to Google Cloud...$(NC)"
	./scripts/deploy.sh gcp

deploy-aws: ## Deploy to AWS
	@echo "$(BLUE)Deploying to AWS...$(NC)"
	./scripts/deploy.sh aws

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	python3 -c "from orbcomm_tracker.database import Database; Database().backup_database()"
	@echo "$(GREEN)✅ Database backed up$(NC)"

db-vacuum: ## Optimize database
	@echo "$(BLUE)Optimizing database...$(NC)"
	python3 -c "from orbcomm_tracker.database import Database; Database().vacuum_database()"
	@echo "$(GREEN)✅ Database optimized$(NC)"

sync: ## Run manual sync
	@echo "$(BLUE)Running email sync...$(NC)"
	python3 run_sync.py --inbox 2

health-check: ## Check application health
	@echo "$(BLUE)Checking application health...$(NC)"
	@curl -s http://localhost:5000/health | python3 -m json.tool || echo "$(YELLOW)⚠️  Application not running$(NC)"

metrics: ## View Prometheus metrics
	@echo "$(BLUE)Fetching metrics...$(NC)"
	@curl -s http://localhost:5000/metrics || echo "$(YELLOW)⚠️  Metrics not available$(NC)"

version: ## Show version information
	@echo "ORBCOMM Service Tracker v1.1.0"
	@echo "Python: $$(python3 --version)"
	@echo "Flask: $$(python3 -c 'import flask; print(flask.__version__)')"

all: clean install test lint ## Run all checks

ci: install-dev lint test-cov security ## Run CI pipeline locally

.PHONY: all ci
