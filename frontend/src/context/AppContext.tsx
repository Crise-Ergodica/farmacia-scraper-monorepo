import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { filterOptions, MedicineCategory } from '../data/mockData';
import { Medicamento } from '../types/api';

type SessionMode = 'guest' | 'authenticated';

// Adaptado para usar chaves correspondentes ao backend
type SearchRow = {
  medicineId: number;
  medicineNome: string;
  farmaciaId: number;
  preco: number;
};

type AppContextValue = {
  medicines: Medicamento[];
  isLoading: boolean;
  sessionMode: SessionMode;
  favoriteIds: number[];
  recentIds: number[];
  selectedFilters: MedicineCategory[];
  filterOptions: MedicineCategory[];
  continueAsGuest: () => void;
  signIn: (email?: string) => void;
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

const API_URL = "http://127.0.0.1:8000";

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [medicines, setMedicines] = useState<Medicamento[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  const [sessionMode, setSessionMode] = useState<SessionMode>('guest');
  // IDs mockados temporariamente alterados para numbers para não quebrar a UI
  const [favoriteIds, setFavoriteIds] = useState<number[]>([2, 5, 9, 3, 6]);
  const [recentIds, setRecentIds] = useState<number[]>([1, 2, 3]);
  const [selectedFilters, setSelectedFilters] = useState<MedicineCategory[]>([]);

  // Carrega o catálogo do backend ao inicializar o app
  useEffect(() => {
    const fetchCatalogo = async () => {
      try {
        const response = await fetch(`${API_URL}/catalogo/`);
        if (!response.ok) throw new Error('Falha ao buscar catálogo');
        const data = await response.json();
        setMedicines(data);
      } catch (error) {
        console.error("Erro na integração com FastAPI:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCatalogo();
  }, []);

  const continueAsGuest = () => setSessionMode('guest');
  const signIn = () => setSessionMode('authenticated');

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

  // Função auxiliar para encontrar o menor preço entre as ofertas
  const getLowestPrice = (medicine: Medicamento) => {
    if (!medicine.ofertas || medicine.ofertas.length === 0) return Infinity;
    return Math.min(...medicine.ofertas.map(o => Number(o.preco)));
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

    // Transição de lógica: Como "Medicamento" agora só tem "exige_receita" boolean
    // em vez de um array de strings complexas, fazemos uma filtragem básica.
    return list.filter((medicine) => {
      if (selectedFilters.includes('Controlados') && medicine.exige_receita) return true;
      if (selectedFilters.includes('Venda livre') && !medicine.exige_receita) return true;
      // Expanda conforme o banco de dados ganhar colunas de categoria
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
    favoriteIds,
    recentIds,
    selectedFilters,
    filterOptions,
    continueAsGuest,
    signIn,
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