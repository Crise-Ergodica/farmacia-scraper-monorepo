import React, { createContext, useContext } from 'react';

import { SessionMode, useAuthSession } from '../hooks/useAuthSession';
import { useCatalogState } from '../hooks/useCatalogState';
import { useFavoritesState } from '../hooks/useFavoritesState';

export type { FilterKind, FilterOption } from '../services/catalog';
export type { User, LoginResult, RegisterPayload, RegisterResult } from '../hooks/useAuthSession';
export type { SessionMode };

const SessionContext = createContext<ReturnType<typeof useAuthSession> | null>(null);
const CatalogContext = createContext<ReturnType<typeof useCatalogState> | null>(null);
const FavoritesContext = createContext<ReturnType<typeof useFavoritesState> | null>(null);

function required<T>(value: T | null, hookName: string): T {
  if (!value) throw new Error(`${hookName} must be used inside AppProvider`);
  return value;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const session = useAuthSession();
  const catalog = useCatalogState();
  const favorites = useFavoritesState({
    isAuthenticated: session.isAuthenticated,
    sessionVersion: session.sessionVersion,
    rememberMedicines: catalog.rememberMedicines,
    getMedicineById: catalog.getMedicineById,
  });

  return (
    <SessionContext.Provider value={session}>
      <CatalogContext.Provider value={catalog}>
        <FavoritesContext.Provider value={favorites}>{children}</FavoritesContext.Provider>
      </CatalogContext.Provider>
    </SessionContext.Provider>
  );
}

export function useSessionContext() {
  return required(useContext(SessionContext), 'useSessionContext');
}

export function useCatalogContext() {
  return required(useContext(CatalogContext), 'useCatalogContext');
}

export function useFavoritesContext() {
  return required(useContext(FavoritesContext), 'useFavoritesContext');
}

export function useAppContext() {
  return { ...useSessionContext(), ...useCatalogContext(), ...useFavoritesContext() };
}
