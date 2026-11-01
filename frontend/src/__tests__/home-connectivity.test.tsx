import React from 'react';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';

import HomeScreen from '../app/(app)/home';
import { useCatalogContext } from '../context/AppContext';
import { api } from '../services/api';

jest.mock('expo-router', () => ({ useRouter: () => ({ push: jest.fn() }) }));
jest.mock('../context/AppContext', () => ({ useCatalogContext: jest.fn() }));
jest.mock('../components/Screen', () => {
  const React = jest.requireActual<typeof import('react')>('react');
  const { View } = jest.requireActual<typeof import('react-native')>('react-native');
  return { Screen: ({ children }: { children: React.ReactNode }) => React.createElement(View, null, children) };
});
jest.mock('../components/SearchBar', () => ({ SearchBar: () => null }));
jest.mock('../components/CatalogFiltersSidebar', () => ({ CatalogFiltersSidebar: () => null }));
jest.mock('../components/MedicineCard', () => ({ MedicineCard: () => null }));
jest.mock('../components/FilterChip', () => ({
  FilterChip: ({ label, onPress }: { label: string; onPress: () => void }) => {
    const React = jest.requireActual<typeof import('react')>('react');
    const { Pressable, Text } = jest.requireActual<typeof import('react-native')>('react-native');
    return React.createElement(Pressable, { onPress }, React.createElement(Text, null, label));
  },
}));

const mockedUseCatalogContext = useCatalogContext as jest.Mock;
const mockedApiGet = api.get as jest.Mock;

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function setup(loadCatalogPage: jest.Mock) {
  mockedUseCatalogContext.mockReturnValue({
    markAsViewed: jest.fn(),
    selectedFilters: [],
    selectedPharmacyId: null,
    setSelectedPharmacyId: jest.fn(),
    loadCatalogPage,
  });
  return await render(<HomeScreen />);
}

describe('Home connectivity retry', () => {
  beforeAll(() => {
    Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('retries catalog after a request timeout and exits the error state', async () => {
    const initialCatalog = deferred<{ items: []; total: number }>();
    const retriedCatalog = deferred<{ items: []; total: number }>();
    const initialPharmacies = deferred<{ data: [] }>();
    const retriedPharmacies = deferred<{ data: [] }>();
    const loadCatalogPage = jest.fn().mockReturnValueOnce(initialCatalog.promise).mockReturnValueOnce(retriedCatalog.promise);
    mockedApiGet.mockReturnValueOnce(initialPharmacies.promise).mockReturnValueOnce(retriedPharmacies.promise);
    const screen = await setup(loadCatalogPage);

    await act(async () => {
      initialPharmacies.resolve({ data: [] });
      initialCatalog.reject(new Error('timeout of 15000ms exceeded'));
      await Promise.allSettled([initialPharmacies.promise, initialCatalog.promise]);
    });
    await waitFor(() => expect(screen.getByText('N\u00e3o foi poss\u00edvel carregar os medicamentos.')).toBeTruthy());
    fireEvent.press(screen.getByText('Tentar novamente'));

    await waitFor(() => expect(loadCatalogPage).toHaveBeenCalledTimes(2));
    await act(async () => {
      retriedCatalog.resolve({ items: [], total: 0 });
      retriedPharmacies.resolve({ data: [] });
      await Promise.all([retriedCatalog.promise, retriedPharmacies.promise]);
    });
    expect(screen.queryByText('N\u00e3o foi poss\u00edvel carregar os medicamentos.')).toBeNull();
    expect(screen.getByText('Nenhum medicamento encontrado')).toBeTruthy();
  });

  it('retries the pharmacy request and reloads the catalog at the same time', async () => {
    const initialCatalog = deferred<{ items: []; total: number }>();
    const retriedCatalog = deferred<{ items: []; total: number }>();
    const initialPharmacies = deferred<{ data: [] }>();
    const retriedPharmacies = deferred<{ data: { id: number; nome_fantasia: string }[] }>();
    const loadCatalogPage = jest.fn().mockReturnValueOnce(initialCatalog.promise).mockReturnValueOnce(retriedCatalog.promise);
    mockedApiGet
      .mockReturnValueOnce(initialPharmacies.promise)
      .mockReturnValueOnce(retriedPharmacies.promise);
    const screen = await setup(loadCatalogPage);

    await act(async () => {
      initialCatalog.resolve({ items: [], total: 0 });
      initialPharmacies.reject(new Error('Network Error'));
      await Promise.allSettled([initialCatalog.promise, initialPharmacies.promise]);
    });
    await waitFor(() => expect(screen.getByText('N\u00e3o foi poss\u00edvel carregar as farm\u00e1cias.')).toBeTruthy());
    fireEvent.press(screen.getByText('Tentar novamente'));

    await waitFor(() => expect(mockedApiGet).toHaveBeenCalledTimes(2));
    await act(async () => {
      retriedCatalog.resolve({ items: [], total: 0 });
      retriedPharmacies.resolve({ data: [{ id: 1, nome_fantasia: 'Indiana' }] });
      await Promise.all([retriedCatalog.promise, retriedPharmacies.promise]);
    });
    await waitFor(() => expect(screen.getByText('Indiana')).toBeTruthy());
    expect(loadCatalogPage).toHaveBeenCalledTimes(2);
    expect(screen.queryByText('N\u00e3o foi poss\u00edvel carregar as farm\u00e1cias.')).toBeNull();
  });
});
