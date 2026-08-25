# templates/Makefile — Common commands for the hermes-server project
#
# Copy to project root. Usage: make help, make install, make test, etc.

.PHONY: help install start stop health test test-live clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all components
	cd scripts && bash install.sh

start: ## Start the full stack
	cd scripts && bash start_stack.sh

stop: ## Stop the full stack
	cd scripts && bash stop_stack.sh

health: ## Health check
	cd scripts && bash healthcheck.sh

test: ## Run self-contained API test suite (no live server needed)
	python3 tests/test_api.py

test-live: ## Test a running server at localhost:8000
	curl -sf http://127.0.0.1:8000/health | python3 -m json.tool
	@echo ""
	curl -sf -X POST http://127.0.0.1:8000/chat \
		-H "Content-Type: application/json" \
		-d '{"prompt": "Say hello"}' | python3 -m json.tool

clean: ## Remove virtualenv and cache
	rm -rf .venv __pycache__ api/__pycache__ api/routes/__pycache__
