# Integração Drogasil descontinuada

Em 31/10/2026, o desenvolvimento específico da Drogasil foi removido do código ativo. O Preço Bão permanece com as integrações Indiana, Araújo e Pacheco. Não há coleta, importador, extensão, configuração ou scheduler Drogasil.

Os relatórios, capturas, fixtures e dados de homologação sintéticos exclusivos foram retirados da worktree. Nenhum banco foi acessado ou alterado durante a remoção. O volume PostgreSQL isolado da homologação não foi apagado.

A revisão Alembic `c42a83d1710e` permanece no histórico: a homologação documenta sua aplicação em PostgreSQL isolado e não há confirmação do estado de outros bancos. Não executar downgrade nem excluir tabelas/colunas. Os campos de contexto comercial são mantidos como metadados genéricos para compatibilidade de histórico; a tabela genérica de identidade SKU permanece no ORM para que o Alembic reconheça o esquema legado. Nenhum importador ativo grava nela.
