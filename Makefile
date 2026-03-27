# Documentação Oficial (FSF, por meio do Projeto GNU): 
## https://www.gnu.org/software/make/
## https://www.gnu.org/software/make/manual/html_node/Running.html

# Variáveis Globais
BACKEND_DIR = backend
FRONTEND_DIR = frontend

# Definições do Frontend
NPM = npm

# Comandos de Ajuda
.PHONY: help
help: ## Mostra os comandos disponíveis
	@echo "Comandos disponíveis no Monorepo:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Comandos Globais
.PHONY: setup clean
setup: setup-back setup-front ## Instala as dependências de todo o projeto (Back e Front)

clean: clean-back clean-front ## Remove caches, node_modules e ambientes virtuais

# Backend (FastAPI, Python, Poetry, SQLite)
.PHONY: setup-back run-back migrate-back test-back clean-back scrape-back

setup-back: ## Instala as dependências do backend usando Poetry
	@echo "Configurando ambiente Python com Poetry..."
	cd $(BACKEND_DIR) && poetry install

run-back: ## Roda o servidor FastAPI localmente com hot-reload
	@echo "Iniciando servidor FastAPI..."
	cd $(BACKEND_DIR) && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate-back: ## Roda as migrações do banco de dados para o SQLite
	@echo "Aplicando migrações no banco de dados..."
	cd $(BACKEND_DIR) && poetry run alembic upgrade head

test-back: ## Executa a suíte de testes automatizados
	@echo "Rodando testes do backend..."
	cd $(BACKEND_DIR) && poetry run pytest tests/ -v

scrape-back: ## Dispara o script manual de scraping
	@echo "Iniciando processo de scraping..."
	cd $(BACKEND_DIR) && poetry run python -m app.scrapers.main

clean-back: ## Limpa caches e o ambiente do Poetry
	@echo "Limpando artefatos do backend..."
	cd $(BACKEND_DIR) && poetry env remove --all || true
	find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -r {} +
	find $(BACKEND_DIR) -type d -name ".pytest_cache" -exec rm -r {} +

# Frontend (React Native, Expo)
.PHONY: setup-front run-front ios android clean-front

setup-front: ## Instala as dependências Node.js do Expo
	@echo "Instalando dependências do frontend..."
	cd $(FRONTEND_DIR) && $(NPM) install

run-front: ## Inicia o servidor do Expo
	@echo "Iniciando Expo Bundler..."
	cd $(FRONTEND_DIR) && npx expo start

ios: ## Inicia o aplicativo no simulador do iOS
	@echo "Iniciando no iOS..."
	cd $(FRONTEND_DIR) && npx expo start --ios

android: ## Inicia o aplicativo no emulador do Android
	@echo "Iniciando no Android..."
	cd $(FRONTEND_DIR) && npx expo start --android

clean-front: ## Remove o node_modules e arquivos temporários do Expo
	@echo "Limpando artefatos do frontend..."
	rm -rf $(FRONTEND_DIR)/node_modules
	rm -rf $(FRONTEND_DIR)/.expo