import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { Medicamento } from '../types/api';

type SessionMode = 'guest' | 'authenticated';

export type FilterKind =
  | 'receita'
  | 'categoria'
  | 'laboratorio'
  | 'principio_ativo';

export type FilterOption = {
  id: string;
  label: string;
  value: string;
  type: FilterKind;
};

type SearchRow = {
  medicineId: number;
  medicineNome: string;
  farmaciaId: number;
  preco: number;
};

type LoginResult = {
  ok: boolean;
  message: string;
};

type RegisterPayload = {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
};

type RegisterResult = {
  ok: boolean;
  message: string;
};

export type User = {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
};

type BackendMedicamento = Partial<Medicamento> & {
  name_search?: string;
};

type CatalogoResponse = {
  total?: number;
  limit?: number;
  offset?: number;
  items?: BackendMedicamento[];
};

type FiltrosOpcoesResponse = {
  categorias?: string[];
  laboratorios?: string[];
  principios_ativos?: string[];
};

type AppContextValue = {
  medicines: Medicamento[];
  isLoading: boolean;
  isAuthenticated: boolean;
  token: string | null;
  user: User | null;
  sessionMode: SessionMode;
  currentUserName: string | null;
  currentUserEmail: string | null;
  favoriteIds: number[];
  recentIds: number[];
  selectedFilters: FilterOption[];
  filterOptions: FilterOption[];
  updateProfile: (name: string, email: string) => void;
  continueAsGuest: () => void;
  signIn: (email: string, password: string) => Promise<LoginResult>;
  registerUser: (payload: RegisterPayload) => Promise<RegisterResult>;
  logout: () => void;
  toggleFavorite: (id: number) => void;
  markAsViewed: (id: number) => void;
  toggleFilter: (filter: FilterOption) => void;
  applyFilters: (filters: FilterOption[]) => void;
  clearFilters: () => void;
  getMedicineById: (id: number) => Medicamento | undefined;
  recentMedicines: Medicamento[];
  cheapestMedicines: Medicamento[];
  favoriteMedicines: Medicamento[];
  searchMedicines: (query: string) => Medicamento[];
  buildSearchRows: (query: string) => SearchRow[];
};

const AppContext = createContext<AppContextValue | null>(null);

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const RECEITA_FILTERS: FilterOption[] = [
  {
    id: 'receita:controlados',
    label: 'Controlados',
    value: 'controlados',
    type: 'receita',
  },
  {
    id: 'receita:venda_livre',
    label: 'Venda livre',
    value: 'venda_livre',
    type: 'receita',
  },
];

const FIXED_CATEGORY_FILTERS: FilterOption[] = [
  {
    id: 'categoria:similar',
    label: 'Similar',
    value: 'similar',
    type: 'categoria',
  },
  {
    id: 'categoria:original',
    label: 'Original',
    value: 'original',
    type: 'categoria',
  },
];

function normalizeText(value: unknown) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function isTruthyValue(value: unknown) {
  const normalized = normalizeText(value);

  return (
    value === true ||
    value === 1 ||
    normalized === 'true' ||
    normalized === '1' ||
    normalized === 'sim' ||
    normalized === 's'
  );
}

function onlyUniqueStrings(values: unknown[]) {
  const map = new Map<string, string>();

  for (const value of values) {
    const text = String(value || '').trim();
    const normalized = normalizeText(text);

    if (
      !text ||
      normalized === 'nao informado' ||
      normalized === 'indeterminado' ||
      normalized === 'controlados' ||
      normalized === 'controlado' ||
      normalized === 'medicamento controlado' ||
      normalized === 'medicamentos controlados' ||
      normalized === 'similar' ||
      normalized === 'similares' ||
      normalized === 'original' ||
      normalized === 'referencia' ||
      normalized === 'referente' ||
      normalized === 'medicamento referencia' ||
      normalized === 'medicamento de referencia' ||
      normalized === 'medicamentos referencia' ||
      normalized === 'medicamentos de referencia' ||
      normalized.includes('nao informado') ||
      normalized.includes('pendente') ||
      normalized.includes('indeterminado')
    ) {
      continue;
    }

    if (!map.has(normalized)) {
      map.set(normalized, text);
    }
  }

  return Array.from(map.values()).sort((a, b) => a.localeCompare(b, 'pt-BR'));
}

function makeFilterOption(type: FilterKind, value: string): FilterOption {
  return {
    id: `${type}:${normalizeText(value)}`,
    label: value,
    value,
    type,
  };
}

function mergeFilterOptions(...groups: FilterOption[][]) {
  const map = new Map<string, FilterOption>();

  for (const group of groups) {
    for (const option of group) {
      if (!map.has(option.id)) {
        map.set(option.id, option);
      }
    }
  }

  return Array.from(map.values());
}

function buildFilterOptions(data: FiltrosOpcoesResponse): FilterOption[] {
  const categorias = onlyUniqueStrings(data.categorias || []).map((value) =>
    makeFilterOption('categoria', value)
  );

  const laboratorios = onlyUniqueStrings(data.laboratorios || []).map((value) =>
    makeFilterOption('laboratorio', value)
  );

  const principiosAtivos = onlyUniqueStrings(data.principios_ativos || []).map(
    (value) => makeFilterOption('principio_ativo', value)
  );

  return mergeFilterOptions(
    RECEITA_FILTERS,
    FIXED_CATEGORY_FILTERS,
    categorias,
    laboratorios,
    principiosAtivos
  );
}

function normalizeMedicine(medicine: BackendMedicamento): Medicamento {
  const nome = medicine.nome || medicine.name_search || '';

  return {
    id: Number(medicine.id),
    codigo_barras: medicine.codigo_barras || '',
    nome,
    name_search: medicine.name_search || nome,
    principio_ativo: medicine.principio_ativo || '',
    laboratorio: medicine.laboratorio || '',
    exige_receita: isTruthyValue(medicine.exige_receita),
    categorias: Array.isArray(medicine.categorias)
      ? medicine.categorias.map((category) => String(category))
      : [],
    ofertas: Array.isArray(medicine.ofertas) ? medicine.ofertas : [],
  };
}

function getCatalogoItems(data: CatalogoResponse | BackendMedicamento[]) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data.items)) {
    return data.items;
  }

  return [];
}

function getApiMessage(value: unknown, fallback: string) {
  if (!value) {
    return fallback;
  }

  if (typeof value === 'string') {
    return value;
  }

  if (Array.isArray(value)) {
    const messages = value
      .map((item) => {
        if (typeof item === 'string') {
          return item;
        }

        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg);
        }

        if (item && typeof item === 'object' && 'message' in item) {
          return String((item as { message: unknown }).message);
        }

        return '';
      })
      .filter(Boolean);

    return messages.length ? messages.join('\n') : fallback;
  }

  if (typeof value === 'object' && 'msg' in value) {
    return String((value as { msg: unknown }).msg);
  }

  if (typeof value === 'object' && 'message' in value) {
    return String((value as { message: unknown }).message);
  }

  return fallback;
}

function medicineHasExactCategory(medicine: Medicamento, values: string[]) {
  const normalizedValues = values.map(normalizeText);

  return (medicine.categorias || []).some((category) => {
    const normalizedCategory = normalizeText(category);

    return normalizedValues.includes(normalizedCategory);
  });
}

function medicineIsControlled(medicine: Medicamento) {
  return medicineHasExactCategory(medicine, [
    'controlado',
    'controlados',
    'medicamento controlado',
    'medicamentos controlados',
  ]);
}

function medicineIsSimilar(medicine: Medicamento) {
  return medicineHasExactCategory(medicine, [
    'similar',
    'similares',
    'medicamento similar',
    'medicamentos similares',
  ]);
}

function medicineIsOriginal(medicine: Medicamento) {
  return medicineHasExactCategory(medicine, [
    'original',
    'originais',
    'referencia',
    'referência',
    'referente',
    'medicamento referencia',
    'medicamento referência',
    'medicamento de referencia',
    'medicamento de referência',
    'medicamentos referencia',
    'medicamentos referência',
    'medicamentos de referencia',
    'medicamentos de referência',
  ]);
}

function medicineMatchesFilter(medicine: Medicamento, filter: FilterOption) {
  const filterValue = normalizeText(filter.value);
  const fullFilterText = normalizeText(
    [filter.id, filter.label, filter.value, filter.type].join(' ')
  );

  if (
    fullFilterText.includes('controlado') ||
    fullFilterText.includes('controlados')
  ) {
    return medicineIsControlled(medicine);
  }

  if (
    fullFilterText.includes('similar') ||
    fullFilterText.includes('similares')
  ) {
    return medicineIsSimilar(medicine);
  }

  if (
    fullFilterText.includes('original') ||
    fullFilterText.includes('referencia')
  ) {
    return medicineIsOriginal(medicine);
  }

  if (
    fullFilterText.includes('venda livre') ||
    fullFilterText.includes('venda_livre') ||
    fullFilterText.includes('sem receita') ||
    fullFilterText.includes('isento')
  ) {
    return medicine.exige_receita === false && !medicineIsControlled(medicine);
  }

  if (filter.type === 'receita') {
    return false;
  }

  if (filter.type === 'categoria') {
    return medicineHasExactCategory(medicine, [filter.value, filter.label]);
  }

  if (filter.type === 'laboratorio') {
    return normalizeText(medicine.laboratorio) === filterValue;
  }

  if (filter.type === 'principio_ativo') {
    return normalizeText(medicine.principio_ativo) === filterValue;
  }

  return false;
}

const TOKEN_KEY = 'auth_token';

import * as SecureStore from 'expo-secure-store';

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [medicines, setMedicines] = useState<Medicamento[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOption[]>([
    ...RECEITA_FILTERS,
    ...FIXED_CATEGORY_FILTERS,
  ]);

  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [sessionMode, setSessionMode] = useState<SessionMode>('guest');
  const [currentUserName, setCurrentUserName] = useState<string | null>(null);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);
  const [favoriteIds, setFavoriteIds] = useState<number[]>([]);
  const [recentIds, setRecentIds] = useState<number[]>([1, 2, 3]);
  const [selectedFilters, setSelectedFilters] = useState<FilterOption[]>([]);

  useEffect(() => {
    const fetchCatalogoPage = async (limit: number, offset: number) => {
      const params = new URLSearchParams();

      params.set('limit', String(limit));
      params.set('offset', String(offset));

      const response = await fetch(`${API_URL}/catalogo?${params.toString()}`);

      if (!response.ok) {
        throw new Error('Falha ao buscar catálogo');
      }

      const data: CatalogoResponse | BackendMedicamento[] =
        await response.json();

      return data;
    };

    const fetchCatalogo = async () => {
      const limit = 100;
      let offset = 0;
      let allItems: BackendMedicamento[] = [];

      while (true) {
        const data = await fetchCatalogoPage(limit, offset);
        const items = getCatalogoItems(data);

        allItems = [...allItems, ...items];

        const total = Array.isArray(data)
          ? items.length
          : Number(data.total || 0);

        if (!items.length) {
          break;
        }

        if (!total || offset + limit >= total) {
          break;
        }

        offset += limit;
      }

      return allItems;
    };

    const fetchFiltrosOpcoes = async () => {
      const response = await fetch(`${API_URL}/catalogo/filtros/opcoes`);

      if (!response.ok) {
        throw new Error('Falha ao buscar opções de filtro');
      }

      const data: FiltrosOpcoesResponse = await response.json();

      return buildFilterOptions(data);
    };

    const checkAuth = async () => {
      const storedToken = await SecureStore.getItemAsync(TOKEN_KEY);
      if (storedToken) {
        try {
          const response = await fetch(`${API_URL}/users/me`, {
            headers: { Authorization: `Bearer ${storedToken}` },
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            setToken(storedToken);
            setIsAuthenticated(true);
            setSessionMode('authenticated');
            setCurrentUserName(userData.name || userData.email);
            setCurrentUserEmail(userData.email);
          } else {
            await SecureStore.deleteItemAsync(TOKEN_KEY);
          }
        } catch (error) {
          console.error('Erro ao verificar auth:', error);
        }
      }
    };

    const fetchInitialData = async () => {
      try {
        setIsLoading(true);

        const [catalogo, filtros, _] = await Promise.all([
          fetchCatalogo(),
          fetchFiltrosOpcoes().catch(() =>
            mergeFilterOptions(RECEITA_FILTERS, FIXED_CATEGORY_FILTERS)
          ),
          checkAuth(),
        ]);

        setMedicines(catalogo.map(normalizeMedicine));
        setFilterOptions(filtros);
      } catch (error) {
        console.error('Erro na integração com FastAPI:', error);
        setMedicines([]);
        setFilterOptions(mergeFilterOptions(RECEITA_FILTERS, FIXED_CATEGORY_FILTERS));
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const continueAsGuest = () => {
    setSessionMode('guest');
    setCurrentUserName(null);
    setCurrentUserEmail(null);
    setFavoriteIds([]);
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setIsAuthenticated(false);
    setToken(null);
    setUser(null);
    setSessionMode('guest');
    setCurrentUserName(null);
    setCurrentUserEmail(null);
    setFavoriteIds([]);
  };

  const signIn = async (
    email: string,
    password: string
  ): Promise<LoginResult> => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email.trim());
      formData.append('password', password.trim());

      const response = await fetch(`${API_URL}/auth/jwt/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          ok: false,
          message: getApiMessage(data.detail, 'Não foi possível entrar.'),
        };
      }

      const accessToken = data.access_token;
      await SecureStore.setItemAsync(TOKEN_KEY, accessToken);

      const meResponse = await fetch(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      let name = email;
      if (meResponse.ok) {
        const userData = await meResponse.json();
        setUser(userData);
        name = userData.name || userData.email;
      }

      setToken(accessToken);
      setIsAuthenticated(true);
      setSessionMode('authenticated');
      setCurrentUserName(name);
      setCurrentUserEmail(email);

      return {
        ok: true,
        message: 'Login realizado com sucesso.',
      };
    } catch (error) {
      return {
        ok: false,
        message: 'Erro de conexão com o servidor de autenticação.',
      };
    }
  };

  const registerUser = async (
    payload: RegisterPayload
  ): Promise<RegisterResult> => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nome: payload.name.trim(),
          email: payload.email.trim(),
          password: payload.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          ok: false,
          message: getApiMessage(
            data.detail,
            'Não foi possível concluir o cadastro.'
          ),
        };
      }

      return {
        ok: true,
        message: 'Cadastro enviado com sucesso.',
      };
    } catch (error) {
      return {
        ok: false,
        message: 'Erro de conexão com o servidor de cadastro.',
      };
    }
  };

  const updateProfile = (name: string, email: string) => {
    setCurrentUserName(name.trim());
    setCurrentUserEmail(email.trim());
  };

  const toggleFavorite = (id: number) => {
    if (sessionMode !== 'authenticated') {
      return;
    }

    setFavoriteIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [id, ...current]
    );
  };

  const markAsViewed = (id: number) => {
    setRecentIds((current) =>
      [id, ...current.filter((item) => item !== id)].slice(0, 6)
    );
  };

  const toggleFilter = (filter: FilterOption) => {
    setSelectedFilters((current) =>
      current.some((item) => item.id === filter.id)
        ? current.filter((item) => item.id !== filter.id)
        : [...current, filter]
    );
  };

  const applyFilters = (filters: FilterOption[]) => {
    setSelectedFilters(filters);
  };

  const clearFilters = () => {
    setSelectedFilters([]);
  };

  const getMedicineById = useCallback(
    (id: number) => medicines.find((medicine) => medicine.id === id),
    [medicines]
  );

  const recentMedicines = useMemo(
    () =>
      recentIds
        .map((id) => getMedicineById(id))
        .filter(Boolean) as Medicamento[],
    [recentIds, getMedicineById]
  );

  const getLowestPrice = (medicine: Medicamento) => {
    if (!medicine.ofertas || medicine.ofertas.length === 0) {
      return Infinity;
    }

    return Math.min(...medicine.ofertas.map((offer) => Number(offer.preco)));
  };

  const cheapestMedicines = useMemo(
    () =>
      [...medicines]
        .sort((a, b) => getLowestPrice(a) - getLowestPrice(b))
        .slice(0, 6),
    [medicines]
  );

  const favoriteMedicines = useMemo(
    () =>
      favoriteIds
        .map((id) => getMedicineById(id))
        .filter(Boolean) as Medicamento[],
    [favoriteIds, getMedicineById]
  );

  const applySelectedFilters = useCallback(
    (list: Medicamento[]) => {
      if (!selectedFilters.length) {
        return list;
      }

      return list.filter((medicine) =>
        selectedFilters.some((filter) => medicineMatchesFilter(medicine, filter))
      );
    },
    [selectedFilters]
  );

  const searchMedicines = useCallback(
    (query: string) => {
      const normalized = normalizeText(query);

      const filtered = applySelectedFilters(medicines);

      if (!normalized) {
        return filtered;
      }

      return filtered.filter((medicine) => {
        const searchableText = normalizeText(
          [
            medicine.nome,
            medicine.name_search,
            medicine.principio_ativo,
            medicine.laboratorio,
            medicine.categorias.join(' '),
          ].join(' ')
        );

        return searchableText.includes(normalized);
      });
    },
    [applySelectedFilters, medicines]
  );

  const buildSearchRows = useCallback(
    (query: string) =>
      searchMedicines(query).flatMap((medicine) =>
        (medicine.ofertas || []).map((offer) => ({
          medicineId: medicine.id,
          medicineNome: medicine.nome,
          farmaciaId: offer.farmacia_id,
          preco: Number(offer.preco),
        }))
      ),
    [searchMedicines]
  );

  const value: AppContextValue = {
    medicines,
    isLoading,
    isAuthenticated,
    token,
    user,
    sessionMode,
    currentUserName,
    currentUserEmail,
    favoriteIds,
    recentIds,
    selectedFilters,
    filterOptions,
    updateProfile,
    continueAsGuest,
    signIn,
    registerUser,
    logout,
    toggleFavorite,
    markAsViewed,
    toggleFilter,
    applyFilters,
    clearFilters,
    getMedicineById,
    recentMedicines,
    cheapestMedicines,
    favoriteMedicines,
    searchMedicines,
    buildSearchRows,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);

  if (!context) {
    throw new Error('useAppContext must be used inside AppProvider');
  }

  return context;
}