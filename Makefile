# Variáveis Globais
BACKEND_DIR = backend
FRONTEND_DIR = frontend
NPM = npm
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null || echo "docker compose")

# Variáveis do Pipeline de Dados (podem ser sobrescritas no terminal)
CMED_XLSX ?= data/xls_conformidade_site_20260508_234642408.xlsx
CMED_CSV ?= data/cmed_atual.csv

.PHONY: help setup clean db-up db-down db-reset envs migrate-back setup-back setup-front run-back run-front etl-convert etl-ingest etl-run

help: ## Mostra os comandos disponíveis
	@echo "Comandos disponíveis no Monorepo:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: envs db-up setup-back migrate-back setup-front ## Configura o projeto inteiro pronto para rodar
	@echo "\033[32m\n=== Instalação concluída com sucesso! ===\033[0m"
	@echo "Backend: make run-back"
	@echo "Frontend: make run-front"

envs: ## Cria os arquivos .env a partir dos .env.example
	@echo "\033[33mConfigurando variáveis de ambiente...\033[0m"
	@if [ ! -f $(BACKEND_DIR)/.env ]; then cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; echo "Criado backend/.env"; fi
	@if [ ! -f $(FRONTEND_DIR)/.env ]; then cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env; echo "Criado frontend/.env"; fi

db-up: ## Sobe o banco de dados PostgreSQL via Docker
	@echo "\033[33mSubindo banco de dados...\033[0m"
	$(DOCKER_COMPOSE) -f $(BACKEND_DIR)/docker-compose.yml up -d
	@echo "Aguardando o banco de dados aceitar conexões..."
	@sleep 3 

db-down: ## Derruba o banco de dados e destrói os volumes persistentes
	@echo "\033[31mDerrubando contêineres e limpando volumes persistentes...\033[0m"
	$(DOCKER_COMPOSE) -f $(BACKEND_DIR)/docker-compose.yml down -v

db-reset: db-down db-up migrate-back ## Reseta o banco do zero (destrói, sobe e aplica migrações)
	@echo "\033[32mBanco de dados sanitizado e recriado com sucesso.\033[0m"

setup-back: ## Instala as dependências do backend usando Poetry
	@echo "\033[33mConfigurando ambiente Python...\033[0m"
	cd $(BACKEND_DIR) && poetry install

migrate-back: ## Roda as migrações do banco de dados (Alembic)
	@echo "\033[33mAplicando migrações no banco de dados...\033[0m"
	cd $(BACKEND_DIR) && poetry run alembic upgrade head

setup-front: ## Instala as dependências Node.js do Expo
	@echo "\033[33mInstalando dependências do frontend...\033[0m"
	cd $(FRONTEND_DIR) && $(NPM) install

run-back: ## Inicia o servidor backend (FastAPI) em modo reload
	@echo "\033[33mIniciando API...\033[0m"
	cd $(BACKEND_DIR) && poetry run uvicorn app.main:app --reload

run-front: ## Inicia o projeto frontend (Expo)
	@echo "\033[33mIniciando interface Expo...\033[0m"
	cd $(FRONTEND_DIR) && $(NPM) start

etl-convert: ## Converte a planilha XLSX da CMED para CSV
	@echo "\033[33mConvertendo planilha CMED (XLSX -> CSV)...\033[0m"
	cd $(BACKEND_DIR) && poetry run python scripts/convert_cmed_xls_to_csv.py $(CMED_XLSX) $(CMED_CSV)

etl-ingest: ## Ingesta o arquivo CSV gerado no banco de dados
	@echo "\033[33mIniciando carga de dados no PostgreSQL...\033[0m"
	cd $(BACKEND_DIR) && poetry run python scripts/ingest_anvisa_cmed.py $(CMED_CSV)

etl-run: etl-convert etl-ingest ## Roda o pipeline de dados completo (Conversão + Ingestão)
	@echo "\033[32mPipeline ETL concluído.\033[0m"