# Variáveis Globais
BACKEND_DIR = backend
FRONTEND_DIR = frontend
NPM = npm
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null || echo "docker compose")

.PHONY: help setup clean db-up db-down envs migrate-back setup-back setup-front

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

setup-back: ## Instala as dependências do backend usando Poetry
	@echo "\033[33mConfigurando ambiente Python...\033[0m"
	cd $(BACKEND_DIR) && poetry install

migrate-back: ## Roda as migrações do banco de dados (Alembic)
	@echo "\033[33mAplicando migrações no banco de dados...\033[0m"
	cd $(BACKEND_DIR) && poetry run alembic upgrade head

setup-front: ## Instala as dependências Node.js do Expo
	@echo "\033[33mInstalando dependências do frontend...\033[0m"
	cd $(FRONTEND_DIR) && $(NPM) install