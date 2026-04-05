import React, { createContext, useContext, useMemo, useState } from 'react';

import {
  filterOptions,
  getLowestOffer,
  medicines,
  Medicine,
  MedicineCategory,
} from '../data/mockData';

type SessionMode = 'guest' | 'authenticated';

type SearchRow = {
  medicineId: string;
  medicineName: string;
  pharmacy: string;
  price: number;
};

type AppContextValue = {
  medicines: Medicine[];
  sessionMode: SessionMode;
  favoriteIds: string[];
  recentIds: string[];
  selectedFilters: MedicineCategory[];
  filterOptions: MedicineCategory[];
  continueAsGuest: () => void;
  signIn: (email?: string) => void;
  toggleFavorite: (id: string) => void;
  markAsViewed: (id: string) => void;
  toggleFilter: (filter: MedicineCategory) => void;
  clearFilters: () => void;
  getMedicineById: (id: string) => Medicine | undefined;
  recentMedicines: Medicine[];
  cheapestMedicines: Medicine[];
  favoriteMedicines: Medicine[];
  searchMedicines: (query: string) => Medicine[];
  buildSearchRows: (query: string) => SearchRow[];
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [sessionMode, setSessionMode] = useState<SessionMode>('guest');
  const [favoriteIds, setFavoriteIds] = useState<string[]>(['2', '5', '9', '3', '6']);
  const [recentIds, setRecentIds] = useState<string[]>(['1', '2', '3']);
  const [selectedFilters, setSelectedFilters] = useState<MedicineCategory[]>([]);

  const continueAsGuest = () => setSessionMode('guest');
  const signIn = () => setSessionMode('authenticated');

  const toggleFavorite = (id: string) => {
    setFavoriteIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [id, ...current]
    );
  };

  const markAsViewed = (id: string) => {
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

  const getMedicineById = (id: string) => medicines.find((medicine) => medicine.id === id);

  const recentMedicines = useMemo(
    () => recentIds.map((id) => getMedicineById(id)).filter(Boolean) as Medicine[],
    [recentIds]
  );

  const cheapestMedicines = useMemo(
    () => [...medicines].sort((a, b) => getLowestOffer(a).price - getLowestOffer(b).price).slice(0, 6),
    []
  );

  const favoriteMedicines = useMemo(
    () => favoriteIds.map((id) => getMedicineById(id)).filter(Boolean) as Medicine[],
    [favoriteIds]
  );

  const applyCategoryFilters = (list: Medicine[]) => {
    if (!selectedFilters.length) {
      return list;
    }

    return list.filter((medicine) =>
      medicine.categories.some((category) => selectedFilters.includes(category))
    );
  };

  const searchMedicines = (query: string) => {
    const normalized = query.trim().toLowerCase();
    const filtered = applyCategoryFilters(medicines);

    if (!normalized) {
      return filtered;
    }

    return filtered.filter((medicine) => medicine.name.toLowerCase().includes(normalized));
  };

  const buildSearchRows = (query: string) =>
    searchMedicines(query).flatMap((medicine) =>
      medicine.offers.map((offer) => ({
        medicineId: medicine.id,
        medicineName: medicine.name,
        pharmacy: offer.pharmacy,
        price: offer.price,
      }))
    );

  const value: AppContextValue = {
    medicines,
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
