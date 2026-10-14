import { act, renderHook, waitFor } from '@testing-library/react-native';

import { api } from '../services/api';
import { useFavoritesState } from '../hooks/useFavoritesState';
import { Medicamento } from '../types/api';

const medicine: Medicamento = {
  id: 7, codigo_barras: '', nome: 'Dipirona', name_search: 'Dipirona',
  principio_ativo: 'Dipirona', laboratorio: 'Lab A', exige_receita: false,
  categorias: [], ofertas: [],
};

beforeEach(() => jest.clearAllMocks());

it('loads saved favorites, persists add/remove actions, and keeps the server response as source of truth', async () => {
  let stored: Medicamento[] = [medicine];
  (api.get as jest.Mock).mockImplementation((url: string) => Promise.resolve({
    data: url.endsWith('/medicamentos') ? stored : [],
  }));
  (api.post as jest.Mock).mockImplementation(async () => { stored = [medicine]; });
  (api.delete as jest.Mock).mockImplementation(async () => { stored = []; });
  const { result } = await renderHook(() => useFavoritesState({
    isAuthenticated: true,
    sessionVersion: 1,
    rememberMedicines: jest.fn(),
    getMedicineById: () => medicine,
  }));
  await waitFor(() => expect(result.current.favoriteIds).toEqual([7]));
  expect(result.current.favoriteMedicines[0].nome).toBe('Dipirona');

  await act(async () => { await result.current.toggleFavorite(7); });
  expect(api.delete).toHaveBeenCalledWith('/users/me/favoritos/medicamentos/7');
  expect(result.current.favoriteIds).toEqual([]);

  await act(async () => { await result.current.toggleFavorite(7); });
  expect(api.post).toHaveBeenCalledWith('/users/me/favoritos/medicamentos/7');
  expect(result.current.favoriteIds).toEqual([7]);
});

it('isolates account state across logout and a subsequent login', async () => {
  let stored: Medicamento[] = [medicine];
  (api.get as jest.Mock).mockImplementation((url: string) => Promise.resolve({
    data: url.endsWith('/medicamentos') ? stored : [],
  }));
  const props = {
    isAuthenticated: true,
    sessionVersion: 1,
    rememberMedicines: jest.fn(),
    getMedicineById: () => undefined,
  };
  const { result, rerender } = await renderHook(
    (value: typeof props) => useFavoritesState(value),
    { initialProps: props }
  );
  await waitFor(() => expect(result.current.favoriteIds).toEqual([7]));

  stored = [];
  await rerender({ ...props, isAuthenticated: false, sessionVersion: 2 });
  await waitFor(() => expect(result.current.favoriteIds).toEqual([]));
  await rerender({ ...props, sessionVersion: 3 });
  await waitFor(() => expect(result.current.favoritesLoading).toBe(false));
  expect(result.current.favoriteIds).toEqual([]);
  expect(result.current.favoriteMedicines).toEqual([]);
});

it('keeps existing favorite state when a network sync fails and exposes a retryable error', async () => {
  (api.get as jest.Mock)
    .mockResolvedValueOnce({ data: [medicine] })
    .mockResolvedValueOnce({ data: [] })
    .mockRejectedValueOnce(new Error('offline'));
  const { result } = await renderHook(() => useFavoritesState({
    isAuthenticated: true,
    sessionVersion: 1,
    rememberMedicines: jest.fn(),
    getMedicineById: () => undefined,
  }));
  await waitFor(() => expect(result.current.favoriteIds).toEqual([7]));
  await act(async () => { await result.current.refreshFavorites(); });
  expect(result.current.favoriteIds).toEqual([7]);
  expect(result.current.favoritesError).toMatch(/sincronizar/i);
});

it('exposes loading and empty states while an account has no saved favorites', async () => {
  let resolveMedicines!: (value: { data: Medicamento[] }) => void;
  let resolvePharmacies!: (value: { data: number[] }) => void;
  (api.get as jest.Mock).mockImplementation((url: string) => new Promise((resolve) => {
    if (url.endsWith('/medicamentos')) resolveMedicines = resolve;
    else resolvePharmacies = resolve;
  }));
  const { result } = await renderHook(() => useFavoritesState({
    isAuthenticated: true,
    sessionVersion: 1,
    rememberMedicines: jest.fn(),
    getMedicineById: () => undefined,
  }));
  expect(result.current.favoritesLoading).toBe(true);

  await act(async () => {
    resolveMedicines({ data: [] });
    resolvePharmacies({ data: [] });
    await Promise.resolve();
  });
  await waitFor(() => expect(result.current.favoritesLoading).toBe(false));
  expect(result.current.favoriteMedicines).toEqual([]);
  expect(result.current.favoritesError).toBeNull();
});

it('normalizes association shaped favorites, drops invalid IDs, and deduplicates keys', async () => {
  (api.get as jest.Mock).mockImplementation((url: string) => Promise.resolve({
    data: url.endsWith('/medicamentos') ? [
      { medicamento: medicine },
      { medicamento_id: '7', medicamento: { nome: 'Dipirona sem ID interno' } },
      { id: '7', nome: 'duplicado' },
      { id: 'NaN', nome: 'inválido' },
      { id: 0, nome: 'inválido' },
    ] : [],
  }));
  const { result } = await renderHook(() => useFavoritesState({
    isAuthenticated: true,
    sessionVersion: 1,
    rememberMedicines: jest.fn(),
    getMedicineById: () => undefined,
  }));
  await waitFor(() => expect(result.current.favoritesLoading).toBe(false));
  expect(result.current.favoriteIds).toEqual([7]);
  expect(result.current.favoriteMedicines.map((item) => item.id)).toEqual([7]);
});
