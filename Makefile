# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: help install-deps lint server tests

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-deps: ## Install dependencies
	@echo "Installing dependencies..."
	pip install .

lint: ## Lint the code
	@echo "Linting the code..."
	ruff check

server: ## Start the FastAPI development server
	@echo "Starting FastAPI server..."
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

tests: ## Run all tests using pytest
	@echo "Running tests..."
	pytest

langgraph: ## Run LangGraph for monitoring and debugging
	@echo "Starting LangGraph..."
	langgraph dev