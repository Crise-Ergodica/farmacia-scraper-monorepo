// Interfaces baseadas nos Schemas do FastAPI (catalogo.py e oferta.py)
export interface Oferta {
  id: number;
  farmacia_id: number;
  catalogo_id: number;
  preco: number; 
  quantidade_estoque: number;
  disponivel: boolean;
  url_origem: string;
  imagem_url?: string;
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