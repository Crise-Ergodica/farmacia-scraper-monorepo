$ErrorActionPreference = "Stop" # Regra de Ouro: Aborta no primeiro erro não tratado

# 1 : BLOCO DE AUTO-ELEVAÇÃO PARA ADMINISTRADOR
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-Not $isAdmin) {
    Write-Host "Privilégios de Administrador não detectados. Elevando permissões..." -ForegroundColor Yellow
    # Reabre este exato script em uma nova janela como Administrador
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# 2 : DEFINIÇÃO DO MARCADOR DE ESTADO (Para lidar com reboots)
$resumeMarker = "$env:TEMP\precobao_setup_resume.marker"

if (-not (Test-Path $resumeMarker)) {
    
    # FASE 1: PREPARAÇÃO E REBOOT (WSL e Hyper-V)
    Write-Host "Iniciando a instalação do ambiente de desenvolvimento..." -ForegroundColor Cyan
    Write-Host "Verificando o estado do Windows Subsystem for Linux (WSL) e Virtual Machine Platform..." -ForegroundColor Yellow

    $wsl = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    $vmp = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
    $rebootRequired = $false

    if ($wsl.State -ne 'Enabled') {
        Write-Host "Habilitando WSL..."
        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
        $rebootRequired = $true
    }

    if ($vmp.State -ne 'Enabled') {
        Write-Host "Habilitando Virtual Machine Platform..."
        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
        $rebootRequired = $true
    }

    if ($rebootRequired) {
        Write-Host "=================================================================" -ForegroundColor Red
        Write-Host "ATENÇÃO: Os recursos do WSL foram habilitados, mas o Windows" -ForegroundColor Red
        Write-Host "exige uma reinicialização para que o kernel entre em vigor." -ForegroundColor Red
        Write-Host "Configurando reinício automático e retomada do script..." -ForegroundColor Yellow
        Write-Host "=================================================================" -ForegroundColor Red
        
        # Cria o marcador de estado para pular esta fase no próximo boot
        New-Item -Path $resumeMarker -ItemType File -Force | Out-Null

        # Agenda a reabertura automática do script após você fazer login novamente
        $runOnceCmd = "powershell.exe -WindowStyle Hidden -Command `"Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -NoExit -File ''$PSCommandPath''' -Verb RunAs`""
        Set-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Name "ResumePrecoBaoSetup" -Value $runOnceCmd
        
        Write-Host "O computador será reiniciado em 5 segundos..." -ForegroundColor Red
        Start-Sleep -Seconds 5
        Restart-Computer -Force
        Exit
    }
} else {
    
    # FASE 2: RETOMADA APÓS O REBOOT
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "Retomando a instalação após o reinício..." -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    
    # Limpa o marcador de estado
    Remove-Item -Path $resumeMarker -Force | Out-Null
}


# FASE 3: INSTALAÇÃO DE FERRAMENTAS E DEPENDÊNCIAS
# Função para instalar via winget isolando falhas de busca
function Install-Tool($name, $id) {
    Write-Host "Verificando $name..."
    # Salva o estado de erro temporariamente para não quebrar o script se o pacote não existir
    $originalErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    # Busca string correspondente ocultando os erros padrão do winget
    $check = winget list --id $id --accept-source-agreements 2>&1 | Select-String $id
    
    $ErrorActionPreference = $originalErrorAction

    if ($check) {
        Write-Host "-> $name já está instalado. Pulando..." -ForegroundColor DarkGray
    } else {
        Write-Host "-> Instalando $name..." -ForegroundColor Cyan
        winget install --id $id --accept-package-agreements --accept-source-agreements --silent
    }
}

# Instalação das ferramentas base
Install-Tool "Git" "Git.Git"
Install-Tool "Python 3.11" "Python.Python.3.11"
Install-Tool "Node.js" "OpenJS.NodeJS"
Install-Tool "Docker Desktop" "Docker.DockerDesktop"
Install-Tool "GNU Make" "ezwinports.make"

# Atualização robusta do PATH na sessão atual
Write-Host "Recarregando variáveis de ambiente..." -ForegroundColor Yellow
$machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"

# Instalação do Poetry via instalador oficial
Write-Host "Instalando Poetry..." -ForegroundColor Cyan
Invoke-RestMethod -Uri https://install.python-poetry.org -OutFile install_poetry.py

$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if ($pythonExe) {
    & $pythonExe.Source install_poetry.py
} else {
    # Como $ErrorActionPreference é "Stop", lançar um erro explícito aborta a execução corretamente
    throw "O executável do Python não foi encontrado no PATH atual. A instalação falhou."
}

Remove-Item install_poetry.py -ErrorAction SilentlyContinue

Write-Host "Instalação concluída com sucesso! Seu ambiente está pronto." -ForegroundColor Green