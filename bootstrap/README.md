# `bootstrap/`

O bootstrap, no contexto da arquitetura de repositórios de software, define-se como um script automatizado — ou um conjunto de scripts alojados em um diretório homônimo na raiz do projeto — cuja função estrita é a configuração inicial e determinística do ambiente de desenvolvimento local.

Ele atua como um contrato executável projetado para eliminar integralmente a necessidade de intervenção manual na preparação de um ecossistema de código. Ao ser executado, o processo de bootstrap encarrega-se de tarefas fundamentais, que incluem, mas não se limitam a: instalação de dependências operacionais e bibliotecas, cópia e parametrização de variáveis de ambiente locais e a inicialização de estruturas de dados e conexões locais.

A exigência técnica primária desse componente é a idempotência. O bootstrap deve possuir a capacidade de ser executado sucessivas vezes sem corromper o estado atual do sistema ou gerar redundâncias operacionais. O seu propósito final é garantir que qualquer recurso humano alocado ao projeto atinja o estado de prontidão (o momento exato em que se pode iniciar a escrita e o teste de código) por meio da execução de um único comando, erradicando a subjetividade e a falha humana inerentes a configurações baseadas exclusivamente em documentação textual.

## `setup_linux.sh`

O código apresentado trata-se de um script de provisionamento de infraestrutura em nível de sistema, projetado para distribuições Linux baseadas em Debian. Sua finalidade técnica é automatizar a preparação inicial de uma máquina local para o desenvolvimento de software por meio da instalação não-interativa de pacotes essenciais, motores de contêinerização e gerenciadores de dependências, garantindo assim o estabelecimento de um ambiente de trabalho padronizado e determinístico sem a necessidade de intervenção manual em múltiplas etapas.

```sh
sudo bash ./bootstrap/setup_linux.sh
```

## `setup_windows.ps1`

O código apresentado consiste em um script de provisionamento de infraestrutura em nível de sistema, projetado especificamente para ambientes operacionais Windows. Sua finalidade técnica é automatizar a preparação inicial de uma máquina local para o desenvolvimento de software, exigindo execução com privilégios administrativos e utilizando o gerenciador de pacotes nativo do sistema para realizar a instalação silenciosa de ferramentas essenciais, motores de contêinerização e gerenciadores de dependências, garantindo a atualização imediata das variáveis de ambiente e o estabelecimento de um ambiente de trabalho padronizado e determinístico sem a necessidade de configuração manual etapa por etapa.

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force; .\bootstrap\setup_windows.ps1
```
