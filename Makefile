.PHONY: help install run dev http test lint lint-fix format clean

# Standart buyruq
.DEFAULT_GOAL := help

help: ## Barcha mavjud buyruqlar ro'yxatini ko'rsatish
	@echo "Foydalanish: make [BUYRUQ]"
	@echo ""
	@echo "Mavjud buyruqlar:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Loyiha bog'liqliklarini o'rnatish (uv sync)
	uv sync

run: ## MCP serverni stdio rejimida ishga tushirish
	uv run mcp-sql

dev: ## MCP Inspector (web UI) orqali dev rejimda ishga tushirish
	uv run fastmcp dev inspector src/mcp_sql/main.py

http: ## MCP serverni HTTP transportida ishga tushirish (port 8000)
	uv run fastmcp run src/mcp_sql/main.py --transport http --port 8000

test: ## Barcha testlarni ishga tushirish (pytest)
	uv run pytest

lint: ## Kod sifatini tekshirish (ruff)
	uv run ruff check .

lint-fix: ## Kod xatolarini avtomatik tuzatish (ruff check --fix)
	uv run ruff check --fix .

format: ## Kodni formatlash (ruff format)
	uv run ruff format .

clean: ## Kesh va vaqtinchalik fayllarni tozalash
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
