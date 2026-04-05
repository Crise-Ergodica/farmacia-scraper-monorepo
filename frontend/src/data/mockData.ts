export type MedicineCategory =
  | 'Generico'
  | 'Original'
  | 'Similar'
  | 'Controlados'
  | 'Venda livre';

export type OfferHistory = {
  label: string;
  value: number;
};

export type PharmacyOffer = {
  pharmacy: string;
  price: number;
  history: OfferHistory[];
};

export type Medicine = {
  id: string;
  name: string;
  categories: MedicineCategory[];
  description: string;
  offers: PharmacyOffer[];
};

export const pharmacyColors: Record<string, string> = {
  'Farmácia 1': '#2E7DFF',
  'Farmácia 2': '#E14747',
  'Farmácia 3': '#F39C12',
  'Farmácia 4': '#34A853',
  'Farmácia 5': '#B455FF',
  'Farmácia 6': '#00B7A8',
};

const buildHistory = (base: number, offsetA: number, offsetB: number) => [
  { label: 'Jan', value: Number((base + offsetA).toFixed(2)) },
  { label: 'Fev', value: Number((base + offsetB).toFixed(2)) },
  { label: 'Mar', value: Number(base.toFixed(2)) },
  { label: 'Abr', value: Number((base - 0.4).toFixed(2)) },
];

export const filterOptions: MedicineCategory[] = [
  'Generico',
  'Original',
  'Similar',
  'Controlados',
  'Venda livre',
];

export const medicines: Medicine[] = [
  {
    id: '1',
    name: 'Remédio 1',
    categories: ['Generico', 'Venda livre'],
    description:
      'Medicamento de exemplo para demonstrar a tela inicial, busca, filtros e histórico de preços.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 19.99, history: buildHistory(19.99, 1.1, 0.6) },
      { pharmacy: 'Farmácia 2', price: 29.99, history: buildHistory(29.99, 0.8, 0.3) },
      { pharmacy: 'Farmácia 3', price: 9.99, history: buildHistory(9.99, 0.7, 0.4) },
      { pharmacy: 'Farmácia 4', price: 12.99, history: buildHistory(12.99, 0.5, 0.2) },
      { pharmacy: 'Farmácia 5', price: 11.99, history: buildHistory(11.99, 0.3, 0.1) },
      { pharmacy: 'Farmácia 6', price: 10.99, history: buildHistory(10.99, 0.6, 0.2) },
    ],
  },
  {
    id: '2',
    name: 'Remédio 2',
    categories: ['Original', 'Venda livre'],
    description:
      'Descrição detalhada do produto, com foco em comparação de preços entre farmácias e visualização histórica.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 17.99, history: buildHistory(17.99, 1.0, 0.7) },
      { pharmacy: 'Farmácia 2', price: 29.99, history: buildHistory(29.99, 0.6, 0.4) },
      { pharmacy: 'Farmácia 3', price: 9.99, history: buildHistory(9.99, 0.3, 0.2) },
      { pharmacy: 'Farmácia 4', price: 12.99, history: buildHistory(12.99, 0.8, 0.5) },
      { pharmacy: 'Farmácia 5', price: 11.99, history: buildHistory(11.99, 0.4, 0.2) },
      { pharmacy: 'Farmácia 6', price: 10.99, history: buildHistory(10.99, 0.5, 0.3) },
    ],
  },
  {
    id: '3',
    name: 'Loratadina',
    categories: ['Generico', 'Similar', 'Venda livre'],
    description:
      'Anti-histamínico usado aqui como exemplo de busca, exibindo o mesmo medicamento em várias farmácias.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 17.99, history: buildHistory(17.99, 0.9, 0.4) },
      { pharmacy: 'Farmácia 2', price: 29.99, history: buildHistory(29.99, 0.8, 0.2) },
      { pharmacy: 'Farmácia 3', price: 9.99, history: buildHistory(9.99, 0.4, 0.1) },
      { pharmacy: 'Farmácia 4', price: 12.99, history: buildHistory(12.99, 0.5, 0.3) },
      { pharmacy: 'Farmácia 5', price: 11.99, history: buildHistory(11.99, 0.4, 0.2) },
      { pharmacy: 'Farmácia 6', price: 10.99, history: buildHistory(10.99, 0.4, 0.1) },
    ],
  },
  {
    id: '4',
    name: 'Remédio 4',
    categories: ['Similar', 'Venda livre'],
    description:
      'Produto de demonstração para preencher a vitrine de mais baratos e a grade de favoritos.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 25.99, history: buildHistory(25.99, 0.8, 0.4) },
      { pharmacy: 'Farmácia 2', price: 18.49, history: buildHistory(18.49, 0.5, 0.2) },
      { pharmacy: 'Farmácia 3', price: 16.99, history: buildHistory(16.99, 0.4, 0.2) },
      { pharmacy: 'Farmácia 4', price: 14.99, history: buildHistory(14.99, 0.6, 0.3) },
    ],
  },
  {
    id: '5',
    name: 'Remédio 5',
    categories: ['Controlados'],
    description:
      'Exemplo de item controlado, apenas para representar filtros específicos e categorias distintas.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 37.99, history: buildHistory(37.99, 0.9, 0.5) },
      { pharmacy: 'Farmácia 2', price: 29.99, history: buildHistory(29.99, 0.7, 0.4) },
      { pharmacy: 'Farmácia 3', price: 31.99, history: buildHistory(31.99, 0.6, 0.3) },
    ],
  },
  {
    id: '6',
    name: 'Remédio 6',
    categories: ['Original', 'Venda livre'],
    description:
      'Outro item fictício para compor as telas iniciais e permitir navegação entre cards.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 22.4, history: buildHistory(22.4, 0.7, 0.3) },
      { pharmacy: 'Farmácia 2', price: 24.9, history: buildHistory(24.9, 0.4, 0.2) },
      { pharmacy: 'Farmácia 6', price: 20.7, history: buildHistory(20.7, 0.6, 0.2) },
    ],
  },
  {
    id: '7',
    name: 'Remédio 7',
    categories: ['Generico', 'Venda livre'],
    description:
      'Medicamento com preço intermediário, utilizado para completar a tela de favoritos do protótipo.',
    offers: [
      { pharmacy: 'Farmácia 2', price: 19.99, history: buildHistory(19.99, 0.5, 0.2) },
      { pharmacy: 'Farmácia 4', price: 17.8, history: buildHistory(17.8, 0.5, 0.3) },
      { pharmacy: 'Farmácia 6', price: 18.9, history: buildHistory(18.9, 0.6, 0.3) },
    ],
  },
  {
    id: '8',
    name: 'Remédio 8',
    categories: ['Similar'],
    description:
      'Mais um item fictício para dar volume à listagem de produtos pesquisados e favoritos.',
    offers: [
      { pharmacy: 'Farmácia 1', price: 26.99, history: buildHistory(26.99, 0.8, 0.4) },
      { pharmacy: 'Farmácia 3', price: 22.3, history: buildHistory(22.3, 0.5, 0.3) },
      { pharmacy: 'Farmácia 5', price: 20.9, history: buildHistory(20.9, 0.7, 0.3) },
    ],
  },
  {
    id: '9',
    name: 'Remédio 9',
    categories: ['Venda livre'],
    description:
      'Item simples para completar a grade da tela de favoritos com diferentes faixas de preço.',
    offers: [
      { pharmacy: 'Farmácia 4', price: 12.99, history: buildHistory(12.99, 0.5, 0.2) },
      { pharmacy: 'Farmácia 6', price: 13.2, history: buildHistory(13.2, 0.4, 0.1) },
    ],
  },
];

export const getLowestOffer = (medicine: Medicine) =>
  [...medicine.offers].sort((a, b) => a.price - b.price)[0];

export const getSortedOffers = (medicine: Medicine) =>
  [...medicine.offers].sort((a, b) => a.price - b.price);
