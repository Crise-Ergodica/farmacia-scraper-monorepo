import { useCallback, useEffect, useRef, useState } from 'react';

import { api } from '../services/api';
import { normalizeMedicine } from '../services/catalog';
import { Medicamento } from '../types/api';

function extractId(item: unknown, keys: string[]): number | undefined {
  if (typeof item === 'number' || typeof item === 'string') {
    const id = Number(item);
    return Number.isSafeInteger(id) && id > 0 ? id : undefined;
  }
  if (!item || typeof item !== 'object') return undefined;
  const record = item as Record<string, unknown>;
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'number' || typeof value === 'string') {
      const id = Number(value);
      if (Number.isSafeInteger(id) && id > 0) return id;
    }
  }
  return undefined;
}

function normalizeFavorite(item: unknown): Medicamento | undefined {
  if (!item || typeof item !== 'object') return undefined;
  const record = item as Record<string, unknown>;
  const nested = record.medicamento ?? record.catalogo ?? record.produto;
  const value = nested && typeof nested === 'object' ? nested : record;
  const medicineId =
    extractId(value, ['id', 'medicamento_id', 'catalogo_id']) ??
    extractId(record, ['medicamento_id', 'catalogo_id']);
  if (!medicineId) return undefined;
  return normalizeMedicine({ ...(value as Record<string, unknown>), id: medicineId } as Partial<Medicamento>);
}

function extractIds(data: unknown, keys: string[]): number[] {
  if (!Array.isArray(data)) return [];
  return [...new Set(data.map((item) => extractId(item, keys)).filter((id): id is number => id !== undefined))];
}

type FavoritesOptions = {
  isAuthenticated: boolean;
  sessionVersion: number;
  rememberMedicines: (items: Medicamento[]) => void;
  getMedicineById: (id: number) => Medicamento | undefined;
};

export function useFavoritesState({
  isAuthenticated,
  sessionVersion,
  rememberMedicines,
  getMedicineById,
}: FavoritesOptions) {
  const [favoriteIds, setFavoriteIds] = useState<number[]>([]);
  const [favoritePharmacyIds, setFavoritePharmacyIds] = useState<number[]>([]);
  const [favoriteMedicines, setFavoriteMedicines] = useState<Medicamento[]>([]);
  const [favoritesLoading, setFavoritesLoading] = useState(false);
  const [favoritesError, setFavoritesError] = useState<string | null>(null);
  const pending = useRef(new Set<string>());
  const syncSerial = useRef({ medicine: 0, pharmacy: 0 });
  const epoch = useRef(sessionVersion);
  const rememberMedicinesRef = useRef(rememberMedicines);
  const getMedicineByIdRef = useRef(getMedicineById);
  rememberMedicinesRef.current = rememberMedicines;
  getMedicineByIdRef.current = getMedicineById;

  const syncMedicines = useCallback(async () => {
    const version = sessionVersion;
    const serial = ++syncSerial.current.medicine;
    setFavoritesLoading(true);
    try {
      const { data } = await api.get<Medicamento[]>('/users/me/favoritos/medicamentos');
      const normalized = Array.isArray(data)
        ? data.map(normalizeFavorite).filter((item): item is Medicamento => item !== undefined)
        : [];
      const unique = [...new Map(normalized.map((item) => [item.id, item])).values()];
      if (version !== epoch.current || serial !== syncSerial.current.medicine) return;
      setFavoriteIds(unique.map((item) => item.id));
      setFavoriteMedicines(unique);
      rememberMedicinesRef.current(unique);
      setFavoritesError(null);
    } catch {
      if (version === epoch.current && serial === syncSerial.current.medicine) {
        setFavoritesError('Não foi possível sincronizar os favoritos. Tente novamente.');
      }
      throw new Error('favorite_sync_failed');
    } finally {
      if (version === epoch.current && serial === syncSerial.current.medicine) {
        setFavoritesLoading(false);
      }
    }
  }, [sessionVersion]);

  const syncPharmacies = useCallback(async () => {
    const version = sessionVersion;
    const serial = ++syncSerial.current.pharmacy;
    try {
      const { data } = await api.get('/users/me/favoritos/farmacias');
      if (version === epoch.current && serial === syncSerial.current.pharmacy) {
        setFavoritePharmacyIds(extractIds(data, ['id', 'farmacia_id']));
      }
    } catch {
      if (version === epoch.current && serial === syncSerial.current.pharmacy) {
        setFavoritesError('Não foi possível sincronizar as farmácias favoritas.');
      }
      throw new Error('pharmacy_sync_failed');
    }
  }, [sessionVersion]);

  useEffect(() => {
    epoch.current = sessionVersion;
    pending.current.clear();
    if (!isAuthenticated) {
      setFavoriteIds([]);
      setFavoritePharmacyIds([]);
      setFavoriteMedicines([]);
      setFavoritesError(null);
      setFavoritesLoading(false);
      return;
    }
    void Promise.allSettled([syncMedicines(), syncPharmacies()]);
  }, [isAuthenticated, sessionVersion, syncMedicines, syncPharmacies]);

  const refreshFavorites = useCallback(async () => {
    if (!isAuthenticated) return;
    await Promise.allSettled([syncMedicines(), syncPharmacies()]);
  }, [isAuthenticated, syncMedicines, syncPharmacies]);

  const toggleFavorite = useCallback(async (id: number) => {
    if (!isAuthenticated || !Number.isSafeInteger(id) || id <= 0) return;
    const version = sessionVersion;
    const key = `${version}:medicine:${id}`;
    if (pending.current.has(key)) return;
    pending.current.add(key);
    const removing = favoriteIds.includes(id);
    let committed = false;
    setFavoritesError(null);
    try {
      if (removing) {
        await api.delete(`/users/me/favoritos/medicamentos/${id}`);
        committed = true;
        if (version === epoch.current) {
          setFavoriteIds((current) => current.filter((item) => item !== id));
          setFavoriteMedicines((current) => current.filter((item) => item.id !== id));
        }
      } else {
        await api.post(`/users/me/favoritos/medicamentos/${id}`);
        committed = true;
        if (version === epoch.current) {
          setFavoriteIds((current) => current.includes(id) ? current : [id, ...current]);
          const medicine = getMedicineByIdRef.current(id);
          if (medicine) setFavoriteMedicines((current) =>
            current.some((item) => item.id === id) ? current : [medicine, ...current]
          );
        }
        await syncMedicines();
      }
    } catch {
      if (version === epoch.current) setFavoritesError(committed
        ? 'Favorito salvo, mas a lista precisa ser sincronizada novamente.'
        : 'Não foi possível salvar o favorito. Tente novamente.');
    } finally {
      pending.current.delete(key);
    }
  }, [favoriteIds, isAuthenticated, sessionVersion, syncMedicines]);

  const togglePharmacyFavorite = useCallback(async (id: number) => {
    if (!isAuthenticated || !Number.isSafeInteger(id) || id <= 0) return;
    const version = sessionVersion;
    const key = `${version}:pharmacy:${id}`;
    if (pending.current.has(key)) return;
    pending.current.add(key);
    const removing = favoritePharmacyIds.includes(id);
    let committed = false;
    try {
      if (removing) {
        await api.delete(`/users/me/favoritos/farmacias/${id}`);
        committed = true;
        if (version === epoch.current) setFavoritePharmacyIds((current) => current.filter((item) => item !== id));
      } else {
        await api.post(`/users/me/favoritos/farmacias/${id}`);
        committed = true;
        if (version === epoch.current) setFavoritePharmacyIds((current) => current.includes(id) ? current : [id, ...current]);
        await syncPharmacies();
      }
    } catch {
      if (version === epoch.current) setFavoritesError(committed
        ? 'Farmácia salva, mas a lista precisa ser sincronizada novamente.'
        : 'Não foi possível salvar a farmácia favorita.');
    } finally {
      pending.current.delete(key);
    }
  }, [favoritePharmacyIds, isAuthenticated, sessionVersion, syncPharmacies]);

  return {
    favoriteIds, favoritePharmacyIds, favoriteMedicines, favoritesLoading,
    favoritesError, refreshFavorites, toggleFavorite, togglePharmacyFavorite,
  };
}
