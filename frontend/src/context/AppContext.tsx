import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { filterOptions, MedicineCategory } from '../data/mockData';
import { Medicamento } from '../types/api';

type SessionMode = 'guest' | 'authenticated';

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

type BackendMedicamento = Partial<Omit<Medicamento, 'categorias' | 'ofertas'>> & {
  name_search?: string;
  categorias?: string[];
  ofertas?: Medicamento['ofertas'];
};

type CatalogoResponse = {
  total?: number;
  limit?: number;
  offset?: number;
  items?: BackendMedicamento[];
};

type AppContextValue = {
  medicines: Medicamento[];
  isLoading: boolean;
  sessionMode: SessionMode;
  currentUserName: string | null;
  currentUserEmail: string | null;
  favoriteIds: number[];
  recentIds: number[];
  selectedFilters: MedicineCategory[];
  filterOptions: MedicineCategory[];
  continueAsGuest: () => void;
  signIn: (email: string, password: string) => Promise<LoginResult>;
  registerUser: (payload: RegisterPayload) => Promise<RegisterResult>;
  logout: () => void;
  toggleFavorite: (id: number) => void;
  markAsViewed: (id: number) => void;
  toggleFilter: (filter: MedicineCategory) => void;
  applyFilters: (filters: MedicineCategory[]) => void;
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

const normalizeText = (value: unknown) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

const normalizeMedicine = (medicine: BackendMedicamento): Medicamento => {
  const nome = medicine.nome || medicine.name_search || '';

  return {
    id: Number(medicine.id),
    codigo_barras: medicine.codigo_barras || '',
    nome,
    principio_ativo: medicine.principio_ativo || '',
    laboratorio: medicine.laboratorio || '',
    exige_receita: Boolean(medicine.exige_receita),
    categorias: Array.isArray(medicine.categorias)
      ? (medicine.categorias as MedicineCategory[])
      : [],
    ofertas: Array.isArray(medicine.ofertas) ? medicine.ofertas : [],
  };
};

const getCatalogoItems = (data: CatalogoResponse | BackendMedicamento[]) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data.items)) {
    return data.items;
  }

  return [];
};

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [medicines, setMedicines] = useState<Medicamento[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionMode, setSessionMode] = useState<SessionMode>('guest');
  const [currentUserName, setCurrentUserName] = useState<string | null>(null);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);
  const [favoriteIds, setFavoriteIds] = useState<number[]>([2, 5, 9, 3, 6]);
  const [recentIds, setRecentIds] = useState<number[]>([1, 2, 3]);
  const [selectedFilters, setSelectedFilters] = useState<MedicineCategory[]>([]);

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
      try {
        setIsLoading(true);

        const limit = 100;
        let offset = 0;
        let allItems: BackendMedicamento[] = [];

        while (true) {
          const data = await fetchCatalogoPage(limit, offset);
          const items = getCatalogoItems(data);

          allItems = [...allItems, ...items];

          const total = Array.isArray(data) ? items.length : Number(data.total || 0);

          if (!items.length) {
            break;
          }

          if (!total || offset + limit >= total) {
            break;
          }

          offset += limit;
        }

        setMedicines(allItems.map(normalizeMedicine));
      } catch (error) {
        console.error('Erro na integração com FastAPI:', error);
        setMedicines([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCatalogo();
  }, []);

  const continueAsGuest = () => {
    setSessionMode('guest');
    setCurrentUserName(null);
    setCurrentUserEmail(null);
  };

  const logout = () => {
    setSessionMode('guest');
    setCurrentUserName(null);
    setCurrentUserEmail(null);
  };

  const signIn = async (
    email: string,
    password: string
  ): Promise<LoginResult> => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          ok: false,
          message: data.detail || 'Não foi possível entrar.',
        };
      }

      setSessionMode('authenticated');
      setCurrentUserName(data.name);
      setCurrentUserEmail(data.email);

      return {
        ok: true,
        message: data.message || 'Login realizado com sucesso.',
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
          name: payload.name.trim(),
          email: payload.email.trim(),
          password: payload.password,
          confirm_password: payload.confirmPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          ok: false,
          message: data.detail || 'Não foi possível concluir o cadastro.',
        };
      }

      return {
        ok: true,
        message: data.message || 'Cadastro enviado com sucesso.',
      };
    } catch (error) {
      return {
        ok: false,
        message: 'Erro de conexão com o servidor de cadastro.',
      };
    }
  };

  const toggleFavorite = (id: number) => {
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

  const toggleFilter = (filter: MedicineCategory) => {
    setSelectedFilters((current) =>
      current.includes(filter)
        ? current.filter((item) => item !== filter)
        : [...current, filter]
    );
  };

  const applyFilters = (filters: MedicineCategory[]) => {
    setSelectedFilters(filters);
  };

  const clearFilters = () => {
    setSelectedFilters([]);
  };

  const getMedicineById = (id: number) => {
    return medicines.find((medicine) => medicine.id === id);
  };

  const recentMedicines = useMemo(
    () =>
      recentIds
        .map((id) => getMedicineById(id))
        .filter(Boolean) as Medicamento[],
    [recentIds, medicines]
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
    [favoriteIds, medicines]
  );

  const applyCategoryFilters = (list: Medicamento[]) => {
    if (!selectedFilters.length) {
      return list;
    }

    return list.filter((medicine) => {
      const categoriesText = normalizeText((medicine.categorias || []).join(' '));

      return selectedFilters.some((filter) => {
        const normalizedFilter = normalizeText(filter);

        if (normalizedFilter.includes('control')) {
          return medicine.exige_receita === true || categoriesText.includes('control');
        }

        if (
          normalizedFilter.includes('venda livre') ||
          normalizedFilter.includes('sem receita')
        ) {
          return medicine.exige_receita === false;
        }

        return categoriesText.includes(normalizedFilter);
      });
    });
  };

  const searchMedicines = (query: string) => {
    const normalized = normalizeText(query);

    const filtered = applyCategoryFilters(medicines);

    if (!normalized) {
      return filtered;
    }

    return filtered.filter((medicine) => {
      const searchableText = normalizeText(
        [
          medicine.nome,
          medicine.principio_ativo,
          medicine.laboratorio,
          medicine.categorias.join(' '),
        ].join(' ')
      );

      return searchableText.includes(normalized);
    });
  };

  const buildSearchRows = (query: string) =>
    searchMedicines(query).flatMap((medicine) =>
      (medicine.ofertas || []).map((offer) => ({
        medicineId: medicine.id,
        medicineNome: medicine.nome,
        farmaciaId: offer.farmacia_id,
        preco: Number(offer.preco),
      }))
    );

  const value: AppContextValue = {
    medicines,
    isLoading,
    sessionMode,
    currentUserName,
    currentUserEmail,
    favoriteIds,
    recentIds,
    selectedFilters,
    filterOptions,
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