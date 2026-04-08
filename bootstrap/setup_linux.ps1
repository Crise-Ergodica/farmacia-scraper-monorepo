# Requer execução como Administrador

# Para rodar:
## Set-ExecutionPolicy Bypass -Scope Process -Force; .\bootstrap\setup_windows.ps1

Write-Host "Iniciando a instalação do ambiente de desenvolvimento..." -ForegroundColor Cyan

# Função para instalar via winget
function Install-Tool($name, $id) {
    Write-Host "Instalando $name..."
    winget install --id $id --accept-package-agreements --accept-source-agreements --silent
}

# Instalação das ferramentas base
Install-Tool "Git" "Git.Git"
Install-Tool "Python" "Python.Python.3.11"
Install-Tool "Docker Desktop" "Docker.DockerDesktop"
Install-Tool "GNU Make" "ezwinports.make"

# Atualizar as variáveis de ambiente na sessão atual
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Instalação do Poetry (exige que o Python já esteja no PATH)
Write-Host "Instalando Poetry..."
Invoke-RestMethod -Uri https://install.python-poetry.org -OutFile install_poetry.py
python install_poetry.py
Remove-Item install_poetry.py

Write-Host "Instalação concluída! Por favor, reinicie o terminal ou o computador." -ForegroundColor Green