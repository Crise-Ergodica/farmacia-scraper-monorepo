import { API_URL, api } from './api';
import { Medicamento } from '../types/api';

export type FilterKind = 'receita' | 'categoria' | 'laboratorio' | 'principio_ativo';
export type FilterOption = { id: string; label: string; value: string; type: FilterKind };
export type CatalogSort = 'relevancia' | 'menor_preco' | 'maior_preco' | 'nome';
export type CatalogPage = { total: number; limit: number; offset: number; items: Medicamento[] };
export type CatalogQuery = {
  query?: string;
  pharmacyId?: number;
  offset?: number;
  limit?: number;
  filters?: FilterOption[];
  sortBy?: CatalogSort;
};

export function normalizeText(value: unknown) {
  return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

const GENERIC_IMAGE_MARKERS = [
  'logo', 'banner', 'placeholder', 'no-image', 'sem-imagem', 'tarjado',
  'caixa-azul', 'caixa-vermelha', 'caixa-medicamento', 'medicamentos-caixa',
  'medicamento-tarjado', 'remedioindiana', 'imagem', 'image-to-upload',
  'caixa-neo-quimica', 'caixa-da-indiana', 'caixa-merck', 'caixa-althaia',
  'etico-otc', 'psicotropico-generico', 'vacinas-caixa',
];
// Araujo sometimes publishes a SKU-linked generic pack image. These are asset
// templates, rather than product allowlists; new SKUs still pass the identity check.
const KNOWN_GENERIC_ASSETS = new Set(['231489_7897705203095_2.webp']);
const NON_IDENTIFYING_TOKENS = new Set([
  'com', 'para', 'de', 'da', 'do', 'e', 'mg', 'mcg', 'ml', 'g', 'ui', 'cpr',
  'cprs', 'comprimido', 'comprimidos', 'capsula', 'capsulas', 'gotas', 'gel',
  'solucao', 'oral', 'generico', 'farmacia', 'produto', 'medicamento', 'www',
]);
function slugTokens(value: string) {
  return normalizeText(value).replace(/[^a-z0-9]+/g, ' ').trim().split(/\s+/).filter(Boolean);
}

function pharmacyHostToken(url: string) {
  try {
    return new URL(url).hostname.split('.').find((part) => !['www', 'i3-imagens-prd', 'vteximg', 'com', 'br'].includes(part)) || '';
  } catch {
    return '';
  }
}

function productIdentityPath(url: string) {
  const parts = new URL(url).pathname.split('/').filter(Boolean);
  let candidate = parts[parts.length - 1] || '';
  if (candidate.toLowerCase() === 'p' || (/^\d+\.html?$/i.test(candidate) && parts.length > 1)) candidate = parts[parts.length - 2] || '';
  return decodeURIComponent(candidate.replace(/\.html?$/i, ''));
}

/** Select only offer images whose descriptive filename agrees with its pharmacy product URL. */
export function resolveMedicineImage(medicine: Medicamento): string | undefined {
  if (medicine.imagem_status === 'verificada' && medicine.imagem_ref?.startsWith('/catalogo/medicamentos/')) {
    return new URL(medicine.imagem_ref, API_URL).toString();
  }
  for (const offer of medicine.ofertas || []) {
    const imageUrl = offer.imagem_url?.trim();
    const productUrl = offer.url_origem?.trim();
    if (!imageUrl || !productUrl || !/^https?:\/\//i.test(imageUrl) || !/^https?:\/\//i.test(productUrl)) continue;
    const imageHost = pharmacyHostToken(imageUrl);
    const productHost = pharmacyHostToken(productUrl);
    if (!imageHost || imageHost !== productHost) continue;

    if (imageHost === 'araujo') {
      try {
        const imageParts = new URL(imageUrl).pathname.split('/').filter(Boolean);
        const productSkuMatch = new URL(productUrl).pathname.match(/\/(\d+)\.html?$/i);
        const fileName = decodeURIComponent(imageParts.at(-1) || '').toLowerCase();
        const imageSku = imageParts.at(-2) || '';
        const imageHasProductIdentifier = fileName.includes(imageSku) || /\d{13,14}/.test(fileName);
        const looksGeneric = GENERIC_IMAGE_MARKERS.some((marker) => fileName.includes(marker));
        if (productSkuMatch?.[1] && imageSku === productSkuMatch[1] && imageHasProductIdentifier && !looksGeneric && !KNOWN_GENERIC_ASSETS.has(fileName)) return imageUrl;
      } catch {
        // Keep unverified pharmacy assets on the neutral placeholder.
      }
      continue;
    }

    let imagePath = '';
    let productPath = '';
    try {
      imagePath = decodeURIComponent(new URL(imageUrl).pathname.split('/').pop() || '').replace(/\.[^.]+(?:\.[^.]+)?$/, '');
      productPath = productIdentityPath(productUrl);
    } catch {
      continue;
    }
    const normalizedImagePath = slugTokens(imagePath).join(' ');
    if (GENERIC_IMAGE_MARKERS.some((marker) => normalizedImagePath.includes(slugTokens(marker).join(' ')))) continue;

    const productTokens = new Set(slugTokens(productPath).filter((token) => token.length >= 5 && !NON_IDENTIFYING_TOKENS.has(token)));
    const imageTokens = slugTokens(imagePath).filter((token) => token.length >= 5 && !NON_IDENTIFYING_TOKENS.has(token));
    if (imageTokens.some((token) => productTokens.has(token))) return imageUrl;
  }
  return undefined;
}

export function normalizeMedicine(raw: Partial<Medicamento> & { name_search?: string }): Medicamento {
  const nome = raw.nome || raw.name_search || '';
  return {
    id: Number(raw.id),
    codigo_barras: raw.codigo_barras || '',
    nome,
    name_search: raw.name_search || nome,
    principio_ativo: raw.principio_ativo || '',
    laboratorio: raw.laboratorio || '',
    exige_receita: Boolean(raw.exige_receita),
    categorias: Array.isArray(raw.categorias) ? raw.categorias.map(String) : [],
    imagem_url: raw.imagem_url || null,
    imagem_ref: raw.imagem_ref || null,
    imagem_fonte: raw.imagem_fonte || null,
    imagem_status: raw.imagem_status || null,
    ofertas: Array.isArray(raw.ofertas) ? raw.ofertas : [],
  };
}

function normalizeUnique(values: unknown[]) {
  const unique = new Map<string, string>();
  for (const value of values) {
    const label = String(value ?? '').trim();
    const key = normalizeText(label);
    if (label && key !== 'nao informado' && key !== 'indeterminado' && !key.includes('pendente')) {
      unique.set(key, label);
    }
  }
  return [...unique.values()].sort((a, b) => a.localeCompare(b, 'pt-BR'));
}

const FIXED_FILTERS: FilterOption[] = [
  { id: 'categoria:controlados', label: 'Controlados', value: 'controlados', type: 'categoria' },
  { id: 'receita:com_receita', label: 'Com receita', value: 'com_receita', type: 'receita' },
  { id: 'receita:venda_livre', label: 'Venda livre', value: 'venda_livre', type: 'receita' },
  { id: 'categoria:similar', label: 'Similar', value: 'similar', type: 'categoria' },
  { id: 'categoria:original', label: 'Original', value: 'original', type: 'categoria' },
];

export async function fetchFilterOptions(): Promise<FilterOption[]> {
  const { data } = await api.get<{ categorias?: string[]; laboratorios?: string[]; principios_ativos?: string[] }>('/catalogo/filtros/opcoes');
  const dynamic: FilterOption[] = [
    ...normalizeUnique(data.categorias || []).map((value) => ({ id: `categoria:${normalizeText(value)}`, label: value, value, type: 'categoria' as const })),
    ...normalizeUnique(data.laboratorios || []).map((value) => ({ id: `laboratorio:${normalizeText(value)}`, label: value, value, type: 'laboratorio' as const })),
    ...normalizeUnique(data.principios_ativos || []).map((value) => ({ id: `principio_ativo:${normalizeText(value)}`, label: value, value, type: 'principio_ativo' as const })),
  ];
  return [...new Map([...FIXED_FILTERS, ...dynamic].map((item) => [item.id, item])).values()];
}

export async function fetchCatalogPage(query: CatalogQuery = {}): Promise<CatalogPage> {
  const params = new URLSearchParams();
  params.set('limit', String(query.limit ?? 20));
  params.set('offset', String(query.offset ?? 0));
  params.set('ordenar', query.sortBy ?? 'relevancia');
  if (query.query?.trim()) params.set('termo_busca', query.query.trim());
  if (query.pharmacyId !== undefined) params.set('farmacia_id', String(query.pharmacyId));
  for (const filter of query.filters || []) params.append('filtros', `${filter.type}:${filter.value}`);
  const { data } = await api.get<{ total: number; limit: number; offset: number; items: (Partial<Medicamento> & { name_search?: string })[] }>(`/catalogo?${params}`);
  return { ...data, items: data.items.map(normalizeMedicine) };
}

export async function fetchMedicine(id: number): Promise<Medicamento> {
  const { data } = await api.get<Partial<Medicamento> & { name_search?: string }>(`/catalogo/medicamentos/${id}`);
  return normalizeMedicine(data);
}

export async function fetchCheapestMedicines(limit = 6): Promise<Medicamento[]> {
  const { data } = await api.get<(Partial<Medicamento> & { name_search?: string })[]>(`/catalogo/mais-baratos?limit=${limit}`);
  return data.map(normalizeMedicine);
}
