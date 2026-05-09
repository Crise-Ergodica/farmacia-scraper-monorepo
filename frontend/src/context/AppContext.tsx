import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

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

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [medicines, setMedicines] = useState<Medicamento[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [sessionMode, setSessionMode] = useState<SessionMode>('guest');
  const [currentUserName, setCurrentUserName] = useState<string | null>(null);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);

  const [favoriteIds, setFavoriteIds] = useState<number[]>([2, 5, 9, 3, 6]);
  const [recentIds, setRecentIds] = useState<number[]>([1, 2, 3]);
  const [selectedFilters, setSelectedFilters] = useState<MedicineCategory[]>([]);

  useEffect(() => {
    const fetchCatalogo = async () => {
      try {
        const response = await fetch(`${API_URL}/catalogo/`);
        if (!response.ok) throw new Error('Falha ao buscar catálogo');
        const data = await response.json();
        setMedicines(data);
      } catch (error) {
        console.error('Erro na integração com FastAPI:', error);
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

  const signIn = async (email: string, password: string): Promise<LoginResult> => {
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

  const registerUser = async (payload: RegisterPayload): Promise<RegisterResult> => {
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
      current.includes(id) ? current.filter((item) => item !== id) : [id, ...current]
    );
  };

  const markAsViewed = (id: number) => {
    setRecentIds((current) => [id, ...current.filter((item) => item !== id)].slice(0, 6));
  };

  const toggleFilter = (filter: MedicineCategory) => {
    setSelectedFilters((current) =>
      current.includes(filter)
        ? current.filter((item) => item !== filter)
        : [...current, filter]
    );
  };

  const clearFilters = () => setSelectedFilters([]);

  const getMedicineById = (id: number) => medicines.find((medicine) => medicine.id === id);

  const recentMedicines = useMemo(
    () => recentIds.map((id) => getMedicineById(id)).filter(Boolean) as Medicamento[],
    [recentIds, medicines]
  );

  const getLowestPrice = (medicine: Medicamento) => {
    if (!medicine.ofertas || medicine.ofertas.length === 0) return Infinity;
    return Math.min(...medicine.ofertas.map((o) => Number(o.preco)));
  };

  const cheapestMedicines = useMemo(
    () => [...medicines].sort((a, b) => getLowestPrice(a) - getLowestPrice(b)).slice(0, 6),
    [medicines]
  );

  const favoriteMedicines = useMemo(
    () => favoriteIds.map((id) => getMedicineById(id)).filter(Boolean) as Medicamento[],
    [favoriteIds, medicines]
  );

  const applyCategoryFilters = (list: Medicamento[]) => {
    if (!selectedFilters.length) {
      return list;
    }

    return list.filter((medicine) => {
      if (selectedFilters.includes('Controlados') && medicine.exige_receita) return true;
      if (selectedFilters.includes('Venda livre') && !medicine.exige_receita) return true;
      return false;
    });
  };

  const searchMedicines = (query: string) => {
    const normalized = query.trim().toLowerCase();
    const filtered = applyCategoryFilters(medicines);

    if (!normalized) {
      return filtered;
    }

    return filtered.filter((medicine) => medicine.nome.toLowerCase().includes(normalized));
  };

  const buildSearchRows = (query: string) =>
    searchMedicines(query).flatMap((medicine) =>
      (medicine.ofertas || []).map((offer) => ({
        medicineId: medicine.id,
        medicineNome: medicine.nome,
        farmaciaId: offer.farmacia_id,
        preco: offer.preco,
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