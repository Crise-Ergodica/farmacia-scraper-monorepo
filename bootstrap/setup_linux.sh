$ErrorActionPreference = "Stop"

# 1 : AUTO-ELEVAÇÃO
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-Not $isAdmin) {
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# 2 : INSTALAÇÃO DO WSL E REBOOT
$resumeMarker = "$env:TEMP\wsl_setup_resume.marker"

if (-not (Test-Path $resumeMarker)) {
    Write-Host "Verificando estado do WSL..." -ForegroundColor Cyan
    
    # Comando simplificado para instalar o WSL (padrão Ubuntu)
    wsl --install
    
    Write-Host "`n=================================================================" -ForegroundColor Red
    Write-Host "O WSL foi habilitado. O Windows PRECISA reiniciar agora." -ForegroundColor Red
    Write-Host "Após o reinício, o Windows abrirá o terminal do Ubuntu para" -ForegroundColor Yellow
    Write-Host "você configurar seu usuário e senha. Depois disso, execute" -ForegroundColor Yellow
    Write-Host "este script novamente para concluir a configuração." -ForegroundColor Yellow
    Write-Host "=================================================================" -ForegroundColor Red
    
    New-Item -Path $resumeMarker -ItemType File -Force | Out-Null
    
    # Agenda a retomada
    $runOnceCmd = "powershell.exe -WindowStyle Normal -Command `"Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -NoExit -File ''$PSCommandPath''' -Verb RunAs`""
    Set-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Name "ResumeWSLSetup" -Value $runOnceCmd
    
    Write-Host "Reiniciando em 10 segundos..." -ForegroundColor Red
    Start-Sleep -Seconds 10
    Restart-Computer -Force
    Exit
}

# 3 : INSTRUÇÕES DO VS CODE E DISPARO DO SCRIPT LINUX
Remove-Item $resumeMarker -Force -ErrorAction SilentlyContinue

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "WSL DETECTADO E ATIVO" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

Write-Host "`nPASSO A PASSO PARA VS CODE:" -ForegroundColor Yellow
Write-Host "1. Instale a extensão 'WSL' (da Microsoft) no seu VS Code local."
Write-Host "2. Clique no ícone azul no canto inferior esquerdo do VS Code."
Write-Host "3. Selecione 'Connect to WSL'."
Write-Host "4. Abra a pasta do projeto dentro do ambiente Linux."

Write-Host "`n-----------------------------------------------------------------"
Write-Host "Iniciando a execução do script Linux dentro do WSL..." -ForegroundColor Cyan

# Converte o caminho do Windows para o caminho do WSL e executa o .sh
$wslPath = wsl wslpath ($PSScriptRoot + "/setup_linux.sh")
wsl bash $wslPath

Write-Host "`nProcesso concluído!" -ForegroundColor Green