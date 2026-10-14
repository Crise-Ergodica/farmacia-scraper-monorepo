# Bootstrap — Provisionamento de Ambiente

Scripts idempotentes para preparar máquinas de desenvolvimento com todas as dependências necessárias ao projeto. O objetivo é eliminar configuração manual e garantir que qualquer pessoa atinja o estado de prontidão com um único comando.

## Princípios

- **Idempotência**: os scripts podem ser executados múltiplas vezes sem corromper o ambiente ou gerar redundâncias.
- **Determinismo**: o resultado final é sempre o mesmo, independente do estado anterior da máquina.
- **Automação total**: nenhuma intervenção manual é necessária durante a execução.

## Scripts disponíveis

### Linux (`setup_linux.sh`)

Provisiona distribuições baseadas em Debian (Ubuntu, Mint, Pop!_OS). Instala:

- Git
- Docker e Docker Compose
- Python 3.11+ e Poetry
- Node.js 18+ e npm

Requer privilégios administrativos:

```sh
sudo bash ./bootstrap/setup_linux.sh
```

### Windows (`setup_windows.ps1`)

Provisiona ambientes Windows usando Chocolatey como gerenciador de pacotes. Instala o mesmo conjunto de ferramentas do script Linux. Requer PowerShell com política de execução liberada e privilégios administrativos:

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force; .\bootstrap\setup_windows.ps1
```

## Após o bootstrap

Com as dependências instaladas, volte à raiz do repositório e execute:

```sh
make setup
```

Este comando cria os arquivos `.env`, sobe o PostgreSQL, instala as dependências do backend e frontend, e aplica as migrações. O projeto fica pronto para desenvolvimento.

## Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| `poetry: command not found` | Poetry não está no PATH após instalação | Reinicie o terminal ou execute `source ~/.bashrc` |
| `docker: permission denied` | Usuário não está no grupo `docker` | Execute `sudo usermod -aG docker $USER` e faça logout/login |
| `npm install` falha com EACCES | Permissões incorretas no diretório global npm | Corrija permissões com `npm config set prefix ~/.npm-global` ou use um gerenciador de versões Node de sua preferência (nvm, fnm, volta) |
| Script Windows falha na política de execução | Política restritiva persistente | Execute como administrador ou altere a política no escopo `LocalMachine` |
| `make db-up` trava no health check | PostgreSQL demorou mais que o esperado | Aguarde ou aumente o `sleep` no Makefile temporariamente |

## Manutenção dos scripts

Ao adicionar novas dependências ao projeto, atualize ambos os scripts (`setup_linux.sh` e `setup_windows.ps1`) para manter a paridade entre plataformas. Teste em uma máquina limpa antes de committer alterações.