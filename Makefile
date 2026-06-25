# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: help install-deps install-observability lint server server-otel tests observability-up observability-down observability-mcp-up

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-deps: ## Install dependencies
	@echo "Installing dependencies..."
	pip install .

install-observability: ## Install OpenTelemetry instrumentation dependencies
	@echo "Installing observability dependencies..."
	pip install ".[observability]"

lint: ## Lint the code
	@echo "Linting the code..."
	ruff check

server: ## Start the FastAPI development server
	@echo "Starting FastAPI server..."
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

server-otel: ## Start the server with OpenTelemetry enabled (Collector on localhost)
	@echo "Starting FastAPI server with telemetry enabled..."
	OTEL_ENABLED=true \
	OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
	OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

observability-up: ## Start the observability stack (collector, tempo, jaeger, prometheus, loki, grafana)
	@echo "Starting observability stack..."
	docker compose up -d otel-collector tempo jaeger prometheus loki grafana

observability-down: ## Stop the observability stack
	@echo "Stopping observability stack..."
	docker compose down

observability-mcp-up: ## Start the optional read-only Grafana MCP service
	@echo "Starting Grafana MCP (read-only)..."
	docker compose --profile observability-mcp up -d grafana-mcp

tests: ## Run all tests using pytest
	@echo "Running tests..."
	pytest

langgraph: ## Run LangGraph for monitoring and debugging
	@echo "Starting LangGraph..."
	langgraph dev