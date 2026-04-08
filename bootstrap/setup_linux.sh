#!/bin/bash
# Requer execução com sudo

# Para rodar:
## sudo bash ./bootstrap/setup_linux.sh

echo -e "\e[36mIniciando a instalação do ambiente de desenvolvimento...\e[0m"

# Atualiza repositórios
sudo apt update && sudo apt upgrade -y

# Instala ferramentas base (Git, Python, Make, curl)
echo "Instalando dependências via apt..."
sudo apt install -y git python3 python3-pip python3-venv make curl

# Instalação do Docker (Motor nativo Linux)
echo "Instalando Docker..."
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER # Adiciona o usuário ao grupo docker para não precisar de sudo

# Instalação do Poetry
echo "Instalando Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

echo -e "\e[32mInstalação concluída! Por favor, reinicie o terminal ou faça logout/login para aplicar os grupos do Docker.\e[0m"