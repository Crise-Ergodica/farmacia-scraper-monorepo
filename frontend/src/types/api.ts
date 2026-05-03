// Interfaces baseadas nos Schemas do FastAPI

export interface Oferta {
  id: number;
  farmacia_id: number;
  catalogo_id: number;
  preco: number;
  quantidade_estoque: number;
  disponivel: boolean;
  url_origem: string;
  imagem_url?: string;
  criado_em?: string;
  atualizado_em?: string | null;

  // opcionais para quando o backend vier com join
  farmacia_nome?: string;
  farmacia?: {
    nome_fantasia?: string;
    razao_social?: string;
  } | null;
}

export interface Medicamento {
  id: number;
  codigo_barras: string;
  nome: string;
  principio_ativo: string;
  laboratorio: string;
  exige_receita: boolean;
  ofertas: Oferta[];
}

export interface HistoricoPrecoPonto {
  data_registro: string;
  preco: number;
}

export interface HistoricoPrecoSerie {
  farmacia_id: number;
  farmacia_nome?: string;
  historico: HistoricoPrecoPonto[];
}