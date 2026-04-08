#!/bin/bash
set -e 

## Requer execução com sudo: 
## sudo bash ./bootstrap/setup_linux.sh

echo -e "\e[36mIniciando a instalação do ambiente de desenvolvimento...\e[0m"

# Identifica a distribuição Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_LIKE=$ID_LIKE
else
    echo -e "\e[31mNão foi possível detectar a distribuição Linux. Abortando.\e[0m"
    exit 1
fi

echo -e "Distribuição detectada: \e[33m$OS\e[0m"

# Função para instalar pacotes via APT (Debian/Ubuntu)
install_apt() {
    sudo apt update && sudo apt upgrade -y
    # Inclui build-essential, libpq-dev, nodejs e o docker-compose-plugin (Compose V2)
    sudo apt install -y git python3 python3-pip python3-venv make curl docker.io docker-compose-plugin build-essential libpq-dev nodejs npm
}

# Função para instalar pacotes via DNF (Fedora/RHEL)
install_dnf() {
    sudo dnf upgrade -y
    # Equivalentes no ecossistema RPM, incluindo o docker-compose-plugin (Compose V2)
    sudo dnf install -y git python3 python3-pip make curl docker docker-compose-plugin gcc postgresql-devel nodejs npm
}

# Função para instalar pacotes via Pacman (Arch Linux/Manjaro)
install_pacman() {
    sudo pacman -Syu --noconfirm
    # No Arch Linux, o pacote docker-compose já entrega a versão moderna em Go
    sudo pacman -S --noconfirm git python python-pip make curl docker docker-compose gcc postgresql-libs nodejs npm
}

# Despachante de gerenciador de pacotes
if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS_LIKE" == *"debian"* ]]; then
    install_apt
elif [[ "$OS" == "fedora" || "$OS_LIKE" == *"fedora"* || "$OS_LIKE" == *"rhel"* ]]; then
    install_dnf
elif [[ "$OS" == "arch" || "$OS_LIKE" == *"arch"* ]]; then
    install_pacman
else
    echo -e "\e[31mGerenciador de pacotes para $OS não mapeado no script.\e[0m"
    exit 1
fi

# Configuração do Docker (Motor nativo Linux)
echo "Configurando serviços do Docker..."
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Instalação do Poetry
echo "Instalando Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

echo -e "\e[32mInstalação concluída com sucesso!\e[0m"
echo -e "\e[33mATENÇÃO:\e[0m Execute o comando \e[1mnewgrp docker\e[0m no seu terminal atual ou reinicie a sessão para aplicar as permissões do grupo Docker sem precisar de sudo."