import { act, renderHook, waitFor } from '@testing-library/react-native';

import { api } from '../services/api';
import { fetchCatalogPage, resolveMedicineImage } from '../services/catalog';
import { useCatalogState } from '../hooks/useCatalogState';
import { Medicamento } from '../types/api';

const item = {
  id: 18, name_search: 'Paracetamol', codigo_barras: '', laboratorio: 'Lab A',
  principio_ativo: 'Paracetamol', exige_receita: false, categorias: [], ofertas: [],
};

beforeEach(() => jest.clearAllMocks());

it('accepts a descriptive product image from the matching pharmacy and rejects generic or mismatched assets', () => {
  const medicine = {
    id: 1, codigo_barras: '7891035010866', nome: 'Strepsils Mel e Limão 16 Pastilhas',
    principio_ativo: '', laboratorio: '', exige_receita: false, categorias: [],
    ofertas: [{
      id: 1, farmacia_id: 1, catalogo_id: 1, preco: 10, quantidade_estoque: 1,
      disponivel: true, url_origem: 'https://www.farmaciaindiana.com.br/strepsils-8-75mg-sabor-mel-e-limao-16-pastilhas/p',
      imagem_url: 'https://farmaciaindiana.vteximg.com.br/arquivos/strepsils-8-75mg-sabor-mel-e-limao-16-pastilhas-1.jpg',
    }],
  };
  expect(resolveMedicineImage(medicine)).toBe(medicine.ofertas[0].imagem_url);
  expect(resolveMedicineImage({ ...medicine, ofertas: [{ ...medicine.ofertas[0], imagem_url: 'https://farmaciaindiana.vteximg.com.br/arquivos/7891035010866.jpg' }] })).toBeUndefined();
  expect(resolveMedicineImage({ ...medicine, ofertas: [{ ...medicine.ofertas[0], imagem_url: 'https://farmaciaindiana.vteximg.com.br/arquivos/MEDICAMENTOS-CAIXA-AZUL-OTC.jpg' }] })).toBeUndefined();
  expect(resolveMedicineImage({ ...medicine, ofertas: [{ ...medicine.ofertas[0], imagem_url: 'https://cdn.example.com/strepsils.jpg' }] })).toBeUndefined();
  expect(resolveMedicineImage({
    ...medicine,
    ofertas: [{ ...medicine.ofertas[0], url_origem: 'https://www.farmaciaindiana.com.br/citrato-sildenafila-50mg-neo-quimica-generico-4-comprimidos/p', imagem_url: 'https://farmaciaindiana.vteximg.com.br/arquivos/Caixa-Neo-Quimica-Generico.jpg' }],
  })).toBeUndefined();
  const araujoOffer = {
    ...medicine.ofertas[0],
    farmacia_id: 2,
    url_origem: 'https://www.araujo.com.br/simeticona-75mgml-cimed-generico-gotas-com-15ml/17332.html',
    imagem_url: 'https://i3-imagens-prd.araujo.com.br/redimensionada/380x380/17332/07896523212319_1.webp',
  };
  expect(resolveMedicineImage({ ...medicine, ofertas: [araujoOffer] })).toBe(araujoOffer.imagem_url);
  const newlyCollectedAraujoOffer = {
    ...araujoOffer,
    url_origem: 'https://www.araujo.com.br/produto-novo/987654.html',
    imagem_url: 'https://i3-imagens-prd.araujo.com.br/redimensionada/380x380/987654/78912345678905_1.webp',
  };
  expect(
    resolveMedicineImage({ ...medicine, ofertas: [newlyCollectedAraujoOffer] }),
  ).toBe(newlyCollectedAraujoOffer.imagem_url);
  expect(resolveMedicineImage({
    ...medicine,
    ofertas: [{ ...araujoOffer, url_origem: 'https://www.araujo.com.br/wegovy-1mg-semaglutida-com-4-doses-injetaveis/101392.html', imagem_url: 'https://i3-imagens-prd.araujo.com.br/redimensionada/380x380/101392/231489_7897705203095_2.webp' }],
  })).toBeUndefined();
});

it('requests only the selected server page and serializes combined filters and search fields', async () => {
  (api.get as jest.Mock).mockResolvedValue({
    data: { total: 37, limit: 12, offset: 12, items: [item] },
  });
  const page = await fetchCatalogPage({
    query: 'paracetamol', pharmacyId: 3, offset: 12, limit: 12,
    sortBy: 'menor_preco',
    filters: [
      { id: 'categoria:similar', label: 'Similar', value: 'similar', type: 'categoria' },
      { id: 'laboratorio:lab-a', label: 'Lab A', value: 'Lab A', type: 'laboratorio' },
    ],
  });
  const requestedUrl = (api.get as jest.Mock).mock.calls[0][0] as string;
  expect(requestedUrl).toContain('limit=12');
  expect(requestedUrl).toContain('offset=12');
  expect(requestedUrl).toContain('termo_busca=paracetamol');
  expect(requestedUrl).toContain('farmacia_id=3');
  expect(requestedUrl).toContain('ordenar=menor_preco');
  expect(requestedUrl.match(/filtros=/g)).toHaveLength(2);
  expect(page.total).toBe(37);
  expect(page.items[0].nome).toBe('Paracetamol');
});

it('keeps a bounded item cache and requests detail by identifier on demand', async () => {
  (api.get as jest.Mock).mockImplementation((url: string) => {
    if (url.startsWith('/catalogo/filtros')) return Promise.resolve({ data: {} });
    if (url.startsWith('/catalogo/mais-baratos')) return Promise.resolve({ data: [] });
    if (url.startsWith('/catalogo/medicamentos/18')) return Promise.resolve({ data: item });
    return Promise.resolve({ data: { total: 1, limit: 20, offset: 0, items: [item] } });
  });
  const { result } = await renderHook(() => useCatalogState());
  let medicine!: Medicamento;
  await act(async () => { medicine = await result.current.loadMedicineById(18); });
  expect(medicine.nome).toBe('Paracetamol');
  expect(api.get).toHaveBeenCalledWith('/catalogo/medicamentos/18');
  await waitFor(() => expect(result.current.getMedicineById(18)?.id).toBe(18));
});
